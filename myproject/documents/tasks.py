from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import boto3
from .models import Document


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
    # S3 클라이언트 초기화
    s3 = boto3.client('s3')

    # 현재 날짜 - 7일 = 만료 기준일
    expiration_date = timezone.now() - timedelta(days=5)

    # 만료된 파일을 찾기 위한 쿼리 작성
    expired_documents = Document.objects.filter(updatedAt__lt=expiration_date)

    for document in expired_documents:
        try:
            # S3에서 파일 삭제
            s3.delete_object(Bucket='lawbotttt', Key=f'documents/{document.pdfUrl.name}')
            # 데이터베이스에서 해당 Document 삭제
            document.delete()
        except Exception as e:
            print(f"Failed to delete {document.pdfUrl.name}: {e}")
