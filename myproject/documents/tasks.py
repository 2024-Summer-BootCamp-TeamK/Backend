import os

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import boto3
from .models import Document


import logging
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

@shared_task
def pdf_to_s3(document_id, file_name, file, data_key_ciphertext):
    try:
        logger.info(f"Starting pdf_to_s3 task for document ID {document_id}")
        document = Document.objects.get(id=document_id)
        content_file = ContentFile(file)
        content_file.data_key_ciphertext = data_key_ciphertext
        document.pdfUrl.save(file_name, content_file)
        document.save()

        return {'status': 'success', 'file_name': file_name}
    except (NoCredentialsError, PartialCredentialsError) as e:
        return {'status': 'failure', 'error': str(e)}

@shared_task()
def upload_file_to_s3(bucket_name, pdf_key, encrypted_data, data_key_ciphertext_base64):
  s3 = boto3.client('s3',
                  aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                  region_name=os.getenv('AWS_S3_REGION_NAME'))
  try:
    s3.put_object(Bucket=bucket_name,
                  Key=pdf_key,
                  Body=encrypted_data,
                  ContentType='application/pdf',
                  ContentDisposition='inline',
                  ACL='public-read',  # 파일을 공개로 설정
                  Metadata={'x-amz-key-v2': data_key_ciphertext_base64}  # 데이터 키를 메타데이터로 추가
                  )
    return {'status': 'success', 'pdf_key': pdf_key}
  except (NoCredentialsError, PartialCredentialsError) as e:
    return {'status': 'failure', 'error': str(e)}


import logging

logger = logging.getLogger(__name__)
@shared_task()
def delete_expired_files():
    #print("1")
    # S3 클라이언트 초기화
    s3 = boto3.client('s3')
    #print("2")

    # 현재 날짜 - 7일 = 만료 기준일
    expiration_date = timezone.now() - timedelta(days=7)
    #print(expiration_date)
    # 만료된 파일을 찾기 위한 쿼리 작성
    expired_documents = Document.objects.filter(updatedAt__lt=expiration_date)
    #print("4")

    # 로그: 만료된 문서 수와 각 문서의 정보 출력
    #print(f"Found {expired_documents.count()} expired documents.")
    for document in expired_documents:
        #print(f"Expired document id={document.id}, pdfUrl={document.pdfUrl.name}")

        try:
            # S3에서 파일 삭제
            response = s3.delete_object(Bucket='lawbotttt', Key=document.pdfUrl.name)
            logger.info(f"Deleted file {document.pdfUrl.name} from S3. Response: {response}")

            # 데이터베이스에서 해당 Document 삭제
            document.delete()
            #print(f"Deleted document {document.id} from database.")
        except Exception as e:
            print(f"Failed to delete {document.pdfUrl.name}: {e}")