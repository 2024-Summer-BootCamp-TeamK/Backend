import boto3
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
from .tasks import pdf_to_s3, upload_file_to_s3
from django.conf import settings

class DocumentUploadView(APIView):
    # 파일이나 폼 형태의 데이터를 처리해야하는 경우 필요!
    parser_classes = [MultiPartParser, FormParser]

    # 스웨거로에서 파일 업로드를 포함하고싶을 땐 밑에처럼 openapi.IN_FORM으 스키마 구성하기!!
    @swagger_auto_schema(
        operation_description="Upload a PDF document",
        manual_parameters=[
            openapi.Parameter('email', openapi.IN_FORM, description="Email address", type=openapi.TYPE_STRING, required=True),
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
        # email은 data로 받아오기
        email = request.data.get('email')

        # pdfFile은 FILES로 받아오기
        pdfFile = request.FILES.get('pdfFile')

        # password는 무작위로 생성
        password = generate_password()

        # 둘 중 하나라도 비어있다면 오류
        if not email or not pdfFile:
            return Response({'error': 'Email and PDF file are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 고유한 파일 이름 생성, uuid4 -> 랜덤 생성 방식
            file_name = f'{uuid.uuid4()}.pdf'

            # Document 객체 생성
            document = Document(email=email, password=password)

            # Document의 pdfUrl 필드에 upload_to 속성이 걸려있기 때문에 바로 ContentFile 형태로 저장해도 url로 저장됨
            # 이게 가능한 이유는 settings.py에서 default_file_storage로 s3를 지정해놨기때문!!
            #document.pdfUrl.save(file_name, ContentFile(pdfFile.read()))
            pdf_to_s3(document, file_name, ContentFile(pdfFile.read()))

            # Document 객체 저장
            document.save()

            # 메일 발송을 위한 객체
            emailMessage = EmailMessage(
                'Title', # 메일 제목
                f'안녕하세여! Password: {password}', # 메일 내용
                to=[email] # 수신자 메일
            )

            # 이메일 발송
            isSuccessed = emailMessage.send()

            # 테스트를 위해 응답으로 pdfUrl을 추가로 지정했음. api 연동할 땐 documentId만!
            return Response({
                'message': 'File uploaded successfully',
                'pdfUrl': document.pdfUrl.url,
                'documentId': document.id,
                'isSuccessed': isSuccessed # 1이면 메일 전송 성공 0이면 실패
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        # 작업에 대한 설명
        operation_description="Retrieve a document by its ID",
        # documentId 경로 parameter 정의
        # IN_PATH를 통해 TYPE_INTEGER형태의 parameter가 경로에 포함되어 있음을 명시
        manual_parameters=[
            openapi.Parameter(
                'documentId',
                openapi.IN_PATH,
                description="ID of the Document",
                type=openapi.TYPE_INTEGER
            )
        ],
        # API 작업의 응답, 문서를 찾은 경우: 200 상태 코드, 못찾은 경우: 404 상태 코드
        responses={
            200: openapi.Response('Document retrieved successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'pdfUrl': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the PDF file')
                }
            )),
            404: 'Document not found.'
        }
    )
    def get(self, request, documentId):
        # documentId가 요청에 포함되어 있는지 확인
        if not documentId:
            return Response({'error': 'Document ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        # DB에서 Document 객체를 조회, 못찾은 경우 404 상태 코드
        document = get_object_or_404(Document, pk=documentId)
        # pdfUrl을 포함한 응답 데이터를 생성하고, 클라이언트에게 반환
        # 성공시 200 상태 코드
        response_data = {
            'pdfUrl': document.pdfUrl.url
        }
        return Response(response_data, status=status.HTTP_200_OK)


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

        bucket_name = 'lawbotttt'
        pdf_key = document.pdfUrl.name

        # 중복된 'documents/' 경로 제거
        pdf_key_parts = pdf_key.split('/')
        unique_pdf_key_parts = []
        for part in pdf_key_parts:
            if part != 'documents' or (part == 'documents' and len(unique_pdf_key_parts) == 0):
                unique_pdf_key_parts.append(part)
        pdf_key = '/'.join(unique_pdf_key_parts)

        try:
            # delay: 작업을 비동기적으로 실행
            result = upload_file_to_s3.delay(bucket_name, pdf_key, uploaded_file.read())

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
            # Pre-signed URL 생성
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            # 문서 파일 키
            file_key = document.pdfUrl.name.split('/')[-1]
            print(file_key)

            # Pre-signed URL 생성
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_key},
                ExpiresIn=3600  # URL의 유효 기간 설정 (60초)
            )
            print(presigned_url)
            return Response({'check': True, 'url': presigned_url}, status=status.HTTP_200_OK)
        else:
            return Response({'check': False}, status=status.HTTP_403_FORBIDDEN)