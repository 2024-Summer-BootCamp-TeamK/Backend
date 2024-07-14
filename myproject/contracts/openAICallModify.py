from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from .utils import prompts

load_dotenv()


def use_ai(contract_text):
    # OpenAI API 키 로드
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        # 사용자 질문 설정
    user_question = f"{contract_text}\n이 당신이 html코드로 반환해 줄 할 계약서 내용 입니다\n반드시 계약서 내 모든 내용은 전부 포함해야 합니다\n"

        # OpenAI 모델 설정
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
    prompt_template = PromptTemplate(
        input_variables=["context"],
        template=prompts.MODIFICATION_PROMPT
    )
    llm_sequence = prompt_template | llm
        # 질문과 검색된 문서 내용을 사용하여 모델에 invoke
    response = llm_sequence.invoke({"context": contract_text, "user_question": user_question})
    raw_result = response.content

    return raw_result



