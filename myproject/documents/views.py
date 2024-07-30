import base64
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Document
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils.generatePassword import generate_password
from .tasks import pdf_to_s3, upload_file_to_s3
import boto3
import os
from django.http import HttpResponse
from .utils.encryption import encrypt_file
from .utils.decryption import decrypt_file
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .serializers import DocumentUploadSerializer

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="PDF 문서 업로드",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'emails': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="이메일 주소 배열"
                ),
                'pdfFile': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY,
                    description="PDF 파일"
                )
            },
            required=['emails', 'pdfFile']
        ),
        responses={
            201: openapi.Response('파일이 성공적으로 업로드 되었습니다', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='성공 메시지'),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING, description='Celery 태스크 ID'),
                    'documentId': openapi.Schema(type=openapi.TYPE_INTEGER, description='문서 ID'),
                    'isSuccessed': openapi.Schema(type=openapi.TYPE_ARRAY, description='이메일 전송 성공 여부',
                                                  items=openapi.Items(type=openapi.TYPE_INTEGER))
                }
            )),
            400: '이메일과 PDF 파일이 필요합니다.'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        emails = serializer.validated_data['emails']
        pdfFile = request.FILES.get('pdfFile')
        password = generate_password()

        if not pdfFile:
            return Response({'error': 'PDF 파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_name = f'{uuid.uuid4()}.pdf'
            file_data = pdfFile.read()
            encrypted_data, data_key_ciphertext = encrypt_file(file_data)

            document = Document(password=password)
            document.save()

            result = pdf_to_s3.delay(document.id, file_name, encrypted_data, data_key_ciphertext)

            isSuccessed_list = []

            for email in emails:
                document_link = f'http://localhost:5173/keyinput/{document.id}'
                context = {
                    'link': document_link,
                    'password': password
                }
                html_content = render_to_string('document_email.html', context)
                text_content = strip_tags(html_content)

                email_message = EmailMultiAlternatives(
                    'LawBot 계약서 공유',
                    text_content,
                    to=[email]
                )
                email_message.attach_alternative(html_content, "text/html")

                isSuccessed = email_message.send()
                isSuccessed_list.append(isSuccessed)

            return Response({
                'message': '파일이 성공적으로 업로드 되었습니다',
                'task_id': result.id,
                'documentId': document.id,
                'isSuccessed': isSuccessed_list
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        # 작업에 대한 설명
        operation_description="Retrieve a document by its ID with password verification",
        # documentId 경로 parameter 정의
        # IN_PATH를 통해 TYPE_INTEGER형태의 parameter가 경로에 포함되어 있음을 명시
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
        # API 작업의 응답, 문서를 찾은 경우: 200 상태 코드, 못찾은 경우: 404 상태 코드
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


    @swagger_auto_schema(
        operation_description='Modifying a document by uploading a new PDF file',
        manual_parameters=[
            openapi.Parameter(
                'documentId',
                openapi.IN_PATH,
                description="ID of the Document",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'pdfFile',
                openapi.IN_FORM,
                description="PDF File",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Document modified successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'pdfUrl': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the updated PDF file'),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID of the asynchronous task')
                }
            )),
            400: 'Bad request. Missing document ID or PDF file.',
            404: 'Document not found.'
        }
    )
    def put(self, request, *args, **kwargs):
        documentId = kwargs.get('documentId')

        if not documentId:
            return Response({'error': 'Document ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        document = get_object_or_404(Document, pk=documentId)

        uploaded_file = request.FILES.get('pdfFile')
        if not uploaded_file:
            return Response({'error': 'No PDF file was uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
        pdf_key = document.pdfUrl.name

        # 중복된 'documents/' 경로 제거
        pdf_key_parts = pdf_key.split('/')
        unique_pdf_key_parts = []
        for part in pdf_key_parts:
            if part != 'documents' or (part == 'documents' and len(unique_pdf_key_parts) == 0):
                unique_pdf_key_parts.append(part)
        pdf_key = '/'.join(unique_pdf_key_parts)

        try:
            # 파일 암호화
            file_data = uploaded_file.read()
            encrypted_data, data_key_ciphertext = encrypt_file(file_data)

            # 데이터 키를 Base64로 인코딩
            data_key_ciphertext_base64 = base64.b64encode(data_key_ciphertext).decode('utf-8')


            # delay: 작업을 비동기적으로 실행
            result = upload_file_to_s3.delay(bucket_name, pdf_key, encrypted_data, data_key_ciphertext_base64)

            response_data = {
                'task_id': result.id,
                'pdfUrl': f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{pdf_key}"
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentAccessView(APIView):

    @swagger_auto_schema(
        operation_description="Check document access by verifying the password.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Document password'),
            }
        ),
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'check': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Check result'),
                }
            )),
            400: 'Bad Request',
            403: 'Forbidden',
        }
    )
    def post(self, request, documentId):
        if not documentId:
            return Response({'error': 'Document Id is required'}, status=status.HTTP_400_BAD_REQUEST)
        document = get_object_or_404(Document, pk=documentId)
        password = request.data.get('password')

        if password == document.password:
            return Response({'check': True}, status=status.HTTP_200_OK)
        else:
            return Response({'check': False}, status=status.HTTP_403_FORBIDDEN)




