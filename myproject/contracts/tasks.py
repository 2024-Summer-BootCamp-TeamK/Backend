import json
import uuid

import fitz
import os
import requests
from celery import shared_task
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework import status
from contracts.models import Type, Contract
from contracts.serializers import ArticleSerializer
from contracts.utils.openAICall import analyze_contract
from .utils.pdfToHtml import pdf_to_html_with_pdfco


@shared_task()
def contract_origin_save(contract_id, pdf_file_name, pdf_content):
    contract = Contract.objects.get(id=contract_id)
    contract.origin_url.save(pdf_file_name, pdf_content)
    contract.save()
    if not contract.origin_url:
        raise ValueError("The file was not saved properly to `origin_url`.")
    return contract.id


@shared_task()
def pdf_to_html_task(contract_id):
    contract = Contract.objects.get(id=contract_id)
    if not contract.origin_url:
        raise ValueError("The 'origin_url' attribute has no file associated with it.")
    pdf_url = contract.origin_url.url

    pdfco_api_key = os.getenv("PDFCO_API_KEY")
    html_content = pdf_to_html_with_pdfco(pdfco_api_key, pdf_url)

    if html_content:
        html_file_name = f'{uuid.uuid4()}.html'

        contract.origin.save(html_file_name, ContentFile(html_content.encode('utf-8')))
        contract.save()
    return contract.id


@shared_task()
def html_extract_content(html_url):
    html_response = requests.get(html_url)
    html_response.raise_for_status()
    return html_response.content.decode('utf-8')


@shared_task()
def pdf_to_text_and_openai(contract_id, pdf_url):
    response = requests.get(pdf_url)
    pdf_content = response.content

    # 페이지 텍스트 추출
    pdf_document = fitz.open(stream=pdf_content, filetype='pdf')
    extracted_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        extracted_text += page.get_text()

    raw_result = analyze_contract(extracted_text)

    # 검토 결과 JSON 형태로 변경
    parsed_result = json.loads(raw_result)
    articles = []
    for i in range(len(parsed_result)):
        article = {
            "contract_id": contract_id,
            "sentence": parsed_result[i].get("sentence", ""),
            "description": parsed_result[i].get("description", ""),
            "law": parsed_result[i].get("law", ""),
            "recommend": parsed_result[i].get("recommend", "")
        }
        # 시리얼라이저를 이용해 데이터 저장
        serializer = ArticleSerializer(data=article)

        if serializer.is_valid():
            article_instance = serializer.save()

            for type_name in parsed_result[i]["types"]:
                type_instance = Type.objects.get(name=type_name)
                article_instance.type.add(type_instance)

            article_data = {
                "articleId": article_instance.id,
                "sentence": article_instance.sentence,
                "types": parsed_result[i].get("types", []),
                "description": article_instance.description,
                "law": article_instance.law,
                "recommend": article_instance.recommend
            }
            articles.append(article_data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return articles
