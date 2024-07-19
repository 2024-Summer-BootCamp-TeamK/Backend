from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from .models import Document
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import EmailMessage
from .utils import generate_password
from .encryption import encrypt_file
from .tasks import pdf_to_s3, upload_file_to_s3


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

            # 파일을 읽고 암호화
            file_data = pdfFile.read()
            encrypted_data = encrypt_file(file_data)

            document = Document(email=email, password=password)

            # 암호화된 파일을 S3에 업로드
            pdf_to_s3(document, file_name, ContentFile(encrypted_data))

            document.save()

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
