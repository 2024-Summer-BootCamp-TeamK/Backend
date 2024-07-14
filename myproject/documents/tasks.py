from celery import shared_task
import boto3

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
