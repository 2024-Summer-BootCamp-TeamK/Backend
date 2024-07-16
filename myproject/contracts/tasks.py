import os
import uuid

from celery import shared_task
from django.core.files.base import ContentFile

from contracts.models import Type
from requests import HTTPError
from .utils.pdfToHtml import pdf_to_html_with_pdfco

@shared_task()
def type_save_task(article, name):
    type_instance = Type.objects.get(name=name)
    article.type.add(type_instance)


@shared_task()
def pdf_to_html_task(contract):

    # S3 url 가져오기
    pdf_url = contract.origin_url.url

    # pdf -> html 코드 변환
    pdfco_api_key = os.getenv('PDFCO_API_KEY')

    html_content = pdf_to_html_with_pdfco(pdfco_api_key, pdf_url)

    # html 코드 S3에 업로드
    if html_content:
        html_file_name = f'{uuid.uuid4()}.html'

        contract.origin.save(html_file_name,ContentFile(html_content.encode('utf-8')))
        contract.save()

