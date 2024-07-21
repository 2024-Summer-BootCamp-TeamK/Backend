import os

import boto3
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Document
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import EmailMessage
from .utils.generatePassword import generate_password
from .utils.encryption import encrypt_file
from .utils.decryption import decrypt_file
from .tasks import pdf_to_s3


class DocumentEncryptionUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload a PDF document",
        manual_parameters=[
            openapi.Parameter('email', openapi.IN_FORM, description="Email address", type=openapi.TYPE_STRING,
                              required=True),
            openapi.Parameter('pdfFile', openapi.IN_FORM, description="PDF file", type=openapi.TYPE_FILE, required=True)
        ],
        responses={
            201: openapi.Response('File uploaded successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    'pdfUrl': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the uploaded PDF file'),
                    'documentId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the document'),
                    'isSuccessed': openapi.Schema(type=openapi.TYPE_INTEGER, description='is email sended?')
                }
            )),
            400: 'Email and PDF file are required.'
        }
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        pdfFile = request.FILES.get('pdfFile')
        password = generate_password()

        if not email or not pdfFile:
            return Response({'error': 'Email and PDF file are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_name = f'{uuid.uuid4()}.pdf'
            file_data = pdfFile.read()
            encrypted_data, data_key_ciphertext = encrypt_file(file_data)

            document = Document(email=email, password=password)
            document.save()

            # 로그 추가: document.id 확인
            print(f"Document ID for Celery task: {document.id}")

            # Celery 태스크 호출
            pdf_to_s3.delay(document.id, file_name, encrypted_data, data_key_ciphertext)
            # Celery 작업이 완료된 후 모델 인스턴스 새로고침
            document.refresh_from_db()
            emailMessage = EmailMessage(
                'Title',
                f'안녕하세요! Password: {password}',
                to=[email]
            )
            isSuccessed = emailMessage.send()

            return Response({
                'message': 'File uploaded successfully',
                'pdfUrl': document.pdfUrl.url,
                'documentId': document.id,
                'isSuccessed': isSuccessed
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentEncryptionView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Retrieve a document by its ID with password verification",
        manual_parameters=[
            openapi.Parameter(
                'documentId',
                openapi.IN_PATH,
                description="ID of the Document",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'X-Password',
                openapi.IN_HEADER,
                description="Password for the document",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Document retrieved successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'file': openapi.Schema(type=openapi.TYPE_STRING, description='Base64 encoded PDF file content'),
                    'fileName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the PDF file')
                }
            )),
            400: 'Bad request. Missing document ID or password.',
            403: 'Forbidden. Incorrect password.',
            404: 'Document not found.'
        }
    )
    def get(self, request, documentId):
        # documentId가 요청에 포함되어 있는지 확인
        if not documentId:
            return Response({'error': 'Document ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 암호 확인
        password = request.headers.get('X-Password')
        if not password:
            return Response({'error': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # DB에서 Document 객체를 조회, 못찾은 경우 404 상태 코드
        document = get_object_or_404(Document, pk=documentId)

        # 비밀번호 확인
        if password != document.password:
            return Response({'error': 'Incorrect password.'}, status=status.HTTP_403_FORBIDDEN)

        # S3에서 암호화된 PDF 파일 다운로드
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION_NAME')
        )
        bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
        file_key = document.pdfUrl.name
        print(file_key)

        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            encrypted_data = response['Body'].read()
            data_key_ciphertext = response['Metadata']['x-amz-key-v2']  # Assuming this is how it's stored

            # 복호화
            decrypted_data = decrypt_file(encrypted_data, data_key_ciphertext)

            # 파일을 반환하는 Response 객체 생성
            response = HttpResponse(decrypted_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={documentId}.pdf'
            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)