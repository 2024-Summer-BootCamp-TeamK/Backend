import os
import boto3
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from base64 import b64decode, b64encode

load_dotenv()

# AWS KMS 클라이언트 생성
kms_client = boto3.client(
    'kms',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_S3_REGION_NAME')  # 지역 정보 추가
)

# PDF 파일 복호화
def decrypt_file(encrypted_data, data_key_ciphertext, kms_client):
    # KMS를 사용하여 암호화된 데이터 키 복호화
    response = kms_client.decrypt(CiphertextBlob=b64decode(data_key_ciphertext))
    data_key_plaintext = response['Plaintext']

    # 데이터 키를 base64로 인코딩하여 Fernet 객체 생성
    data_key_base64 = b64encode(data_key_plaintext).decode('utf-8')
    cipher = Fernet(data_key_base64)

    # 데이터 복호화
    decrypted_data = cipher.decrypt(encrypted_data)

    return decrypted_data
