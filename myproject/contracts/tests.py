from myproject.contracts.utils.openAICall import analyze_contract
from myproject.contracts.utils import toxinPrompts
import os
from dotenv import load_dotenv
import fitz
import requests

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


pdf_url = "https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/5c4a1dcf-ad3f-4186-858a-dac3c127f555.pdf"
response = requests.get(pdf_url, verify=False)
pdf_content = response.content

# 페이지 텍스트 추출
pdf_document = fitz.open(stream=pdf_content, filetype='pdf')
extracted_text = ""
for page_num in range(pdf_document.page_count):
    page = pdf_document.load_page(page_num)
    extracted_text += page.get_text()

result = analyze_contract(extracted_text,toxinPrompts.GUIDELINE_PROMPT,PINECONE_API_KEY,OPENAI_API_KEY)


print(result)