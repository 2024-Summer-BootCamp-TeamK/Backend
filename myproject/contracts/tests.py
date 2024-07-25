from myproject.contracts.utils.openAICall import analyze_contract
from myproject.contracts.utils import toxinPrompts
import os
from dotenv import load_dotenv
import fitz
import requests

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


pdf_url1 = "https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/5c4a1dcf-ad3f-4186-858a-dac3c127f555.pdf" # 우현이 계약서(겸업 금지, 포괄 임금, 일방적 해지, 무단결근)
pdf_url2 = "https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/3c676e33-172d-45a9-bb28-6b11f31edb84.pdf" # 건설 일용 계약서
pdf_url3 = "https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/2731f943-55d9-4d0f-bb38-25cfed927e05.pdf" # 시간 선택제 계약서
pdf_url4 = "https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/802b3c5d-cdc0-42ad-8830-2b534f2b96a2.pdf" # 우현이 계약서 2(다음 근무자, 게시글, CCTV, 임금 체불)


response = requests.get(pdf_url3, verify=False)
pdf_content = response.content

# 페이지 텍스트 추출
pdf_document = fitz.open(stream=pdf_content, filetype='pdf')
extracted_text = ""
for page_num in range(pdf_document.page_count):
    page = pdf_document.load_page(page_num)
    extracted_text += page.get_text()

result = analyze_contract(extracted_text,toxinPrompts.GUIDELINE_PROMPT,PINECONE_API_KEY,OPENAI_API_KEY)


print(result)