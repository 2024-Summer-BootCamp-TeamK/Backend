# custom_storages.py
import boto3
from storages.backends.s3boto3 import S3Boto3Storage
from base64 import b64encode
from dotenv import load_dotenv
import os
load_dotenv()
class CustomS3Boto3Storage(S3Boto3Storage):
    def _save(self, name, content):
        # 파일 저장
        name = super()._save(name, content)

        # 메타데이터 설정
        if hasattr(content, 'data_key_ciphertext'):
            self._set_metadata(name, content.data_key_ciphertext)

        return name

    def _set_metadata(self, name, data_key_ciphertext):
        # 지역을 명시하여 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION_NAME')
        )
        s3_client.copy_object(
            Bucket=self.bucket_name,
            Key=name,
            CopySource={'Bucket': self.bucket_name, 'Key': name},
            MetadataDirective='REPLACE',
            Metadata={
                'x-amz-key-v2': b64encode(data_key_ciphertext).decode('utf-8')
            }
        )
