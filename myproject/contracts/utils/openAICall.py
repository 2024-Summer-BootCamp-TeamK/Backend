import json

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

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def embed_text_with_hf(text):
    # 모델 및 토크나이저 설정
    model_name = "BM-K/KoSimCSE-roberta-multitask"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

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
    index_result = index.query(vector=query_embedding.tolist(), top_k=4, include_metadata=True)
    return [match['metadata']['text'] for match in index_result['matches']]


def search_documents_legal_docs(index, query):
    # 사용자 질문을 임베딩 벡터로 변환하기
    query_embedding = embed_text_with_hf(query)
    if query_embedding.shape != (768,):  # 임베딩 벡터의 크기 확인
        raise ValueError(f"Embedding size is {query_embedding.shape}, expected (768,)")
    result = index.query(vector=query_embedding.tolist(), top_k=4, include_metadata=True)
    return [match['metadata']['세부항목'] for match in result['matches']]


def analyze_contract(contract_text, prompt, PINECONE_API_KEY, OPENAI_API_KEY):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    try:
        # 사용자 질문 설정
        user_question = f"{contract_text}\n이 법률적으로 검토해야 할 계약서 입니다\n"

        index_first = pc.Index("legal-docs")
        initial_search_results = search_documents_legal_docs(index_first, user_question)
        combined_context = " ".join(initial_search_results)

        refined_search_results = []
        index_sec = pc.Index("lawbot")
        refined_search_results.extend(search_documents(index_sec, combined_context))
        context = " ".join(refined_search_results)

        # OpenAI 모델 설정
        llm = ChatOpenAI(model_name="gpt-4-turbo", openai_api_key=OPENAI_API_KEY)
        prompt_template = PromptTemplate(
            input_variables=["context", "user_question"],
            template=prompt
        )
        llm_sequence = prompt_template | llm

        # 질문과 검색된 문서 내용을 사용하여 모델에 invoke
        response = llm_sequence.invoke({"context": context, "user_question": user_question})
        raw_result = response.content
        return raw_result

    except Exception as e:
        print(f"Error in analyze_contract: {str(e)}")
        return json.dumps({'status': 'error', 'message': str(e)})