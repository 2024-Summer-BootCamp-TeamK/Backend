import os
import boto3
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from base64 import b64encode

load_dotenv()

# AWS KMS 클라이언트 생성
kms_client = boto3.client(
    'kms',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_S3_REGION_NAME')  # 지역 정보 추가
)
# KMS 키 ID
kms_key_id = os.getenv('KMS_KEY_ID')


# PDF 파일 암호화
def encrypt_file(file_data):
    # KMS를 사용하여 데이터 키 생성
    response = kms_client.generate_data_key(KeyId=kms_key_id, KeySpec='AES_256')
    data_key_plaintext = response['Plaintext']
    data_key_ciphertext = response['CiphertextBlob']

    # 데이터 키를 사용하여 파일 데이터를 암호화
    cipher = Fernet(b64encode(data_key_plaintext))
    encrypted_data = cipher.encrypt(file_data)

    return encrypted_data, data_key_ciphertext
