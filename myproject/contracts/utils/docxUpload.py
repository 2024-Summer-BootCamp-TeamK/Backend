import uuid

import boto3
import os
from dotenv import load_dotenv
load_dotenv()


def docx_upload(docx):
    # AWS 계정 자격 증명 및 리전 설정
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = os.getenv('AWS_S3_REGION_NAME')  # 예: 'us-east-1'

    # S3 클라이언트 생성
    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key,
                      region_name=region_name)

    # 업로드할 파일 경로
    local_file_path = docx

    # S3 버킷 이름과 파일명 설정
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

    docx_file_name = f'{uuid.uuid4()}.docx'

    s3_file_key = f'docx/{docx_file_name}'  # S3에 저장될 경로와 파일명

    # 파일 업로드
    try:
        s3.upload_file(local_file_path, bucket_name, s3_file_key)
        print(f'{local_file_path} 파일을 {bucket_name} 버킷의 {s3_file_key} 경로에 성공적으로 업로드했습니다.')
        print(s3_file_key)
        return s3_file_key  # 업로드된 파일의 S3 경로 반환
        # docx/df2e61b8-13bb-4a01-b7db-b82a3c113bc2.docx 이런식으로 반환 됨
    except Exception as e:
        print(f'파일 업로드 중 오류 발생: {e}')
    