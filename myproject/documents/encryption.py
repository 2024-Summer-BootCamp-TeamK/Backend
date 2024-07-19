import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# 암호화 키 가져오기
key = os.getenv('ENCRYPTION_KEY').encode()
cipher = Fernet(key)

# 암호화
def encrypt_file(file_data):
    return cipher.encrypt(file_data)

# 복호화
def decrypt_file(encrypted_data):
    return cipher.decrypt(encrypted_data)