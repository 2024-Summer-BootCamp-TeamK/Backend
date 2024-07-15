from celery import shared_task
from django.utils import timezone
import os
import boto3
from .models import Document
import datetime

@shared_task()
def pdf_to_s3(document, file_name, file):
  document.pdfUrl.save(file_name, file)

@shared_task()
def upload_file_to_s3(bucket_name, pdf_key, file_data):
  s3 = boto3.client('s3')
  try:
    s3.put_object(Bucket=bucket_name,
                  Key=pdf_key,
                  Body=file_data,
                  ContentType='application/pdf',
                  ContentDisposition='inline',
                  ACL='public-read'  # 파일을 공개로 설정
                )
    return {'status': 'success', 'pdf_key': pdf_key}
  except Exception as e:
    return {'status': 'failed', 'error': str(e)}

@shared_task
def delete_expired_files():
    documents_path = 'Backend/myproject/documents'

    # 현재 날짜 - 7일 = 만료 기준일
    expiration_date = timezone.now() - datetime.timedelta(weeks=1)

    # documents_path 내의 파일들을 검사하여 만료된 파일 삭제
    for filename in os.listdir(documents_path):
        file_path = os.path.join(documents_path, filename)
        if os.path.isfile(file_path):
            # 파일의 마지막 수정 시간을 가져와서 만료 기준일과 비교
            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mod_time < expiration_date:
                try:
                    os.remove(file_path)
                    print(f"Deleted expired file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

