# custom_storages.py

from storages.backends.s3boto3 import S3Boto3Storage
from base64 import b64encode

class CustomS3Boto3Storage(S3Boto3Storage):
    def _save(self, name, content):
        # 파일 저장
        name = super()._save(name, content)

        # 메타데이터 설정
        if hasattr(content, 'data_key_ciphertext'):
            self._set_metadata(name, content.data_key_ciphertext)

        return name

    def _set_metadata(self, name, data_key_ciphertext):
        s3_client = self.connection.meta.client
        s3_client.copy_object(
            Bucket=self.bucket_name,
            Key=name,
            CopySource={'Bucket': self.bucket_name, 'Key': name},
            MetadataDirective='REPLACE',
            Metadata={
                'x-amz-key-v2': b64encode(data_key_ciphertext).decode('utf-8')
            }
        )
