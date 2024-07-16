from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import torch
from pinecone import Pinecone
from transformers import AutoTokenizer, AutoModel
import numpy as np
import os
from . import mainPrompts

load_dotenv()

# Pinecone API 키와 OpenAI API 키 로드
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 인덱스 이름 설정
index_name = "selective-time"

# 인덱스 열기
index = pc.Index(index_name)

# 모델 및 토크나이저 설정
model_name = "BM-K/KoSimCSE-roberta-multitask"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def embed_text_with_hf(text):
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy().astype(np.float32)
    return embeddings.squeeze()


# 검색 함수 정의
def search_documents(index, query):
    query_embedding = embed_text_with_hf(query)
    if query_embedding.shape != (768,):  # 임베딩 벡터의 크기 확인
        raise ValueError(f"Embedding size is {query_embedding.shape}, expected (768,)")
    index_result = index.query(vector=query_embedding.tolist(), top_k=5, include_metadata=True)
    return [match['metadata']['text'] for match in index_result['matches']]

def search_documents_legal_docs(index, query):
    # 사용자 질문을 임베딩 벡터로 변환하기
    query_embedding = embed_text_with_hf(query)
    if query_embedding.shape != (768,):  # 임베딩 벡터의 크기 확인
        raise ValueError(f"Embedding size is {query_embedding.shape}, expected (768,)")
    result = index.query(vector=query_embedding.tolist(), top_k=6, include_metadata=True)
    return [match['metadata']['세부항목'] for match in result['matches']]

def analyze_contract(contract_text):
    # 사용자 질문 설정
    user_question = f"{contract_text}\n이 법률적으로 검토해야 할 계약서 입니다\n"

    index = pc.Index("legal-docs")
    initial_search_results = search_documents_legal_docs(index, user_question)

    combined_context = " ".join(initial_search_results)

    refined_search_results = []
    index = pc.Index("lawbot")
    refined_search_results.extend(search_documents(index, combined_context))
    # refined_search_results = []
    # for index_name in index_names:
    #     index = pc.Index(index_name)
    #     if index_name == "legal-docs":
    #         refined_search_results.extend(search_documents_legal_docs(index, user_question))
    #     else:
    #         refined_search_results.extend(search_documents(index, user_question))

    # 검색된 문서 텍스트를 모두 하나의 문자열로 결합
    context = " ".join(refined_search_results)

    # OpenAI 모델 설정
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
    prompt_template = PromptTemplate(
        input_variables=["context", "user_question"],
        template=mainPrompts.GUIDELINE_PROMPT
    )
    llm_sequence = prompt_template | llm

    # 질문과 검색된 문서 내용을 사용하여 모델에 invoke
    response = llm_sequence.invoke({"context": context, "user_question": user_question})
    raw_result = response.content
    return raw_result

