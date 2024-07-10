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
                    'documentId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the document')
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

        # 둘 중 하나라도 비어있다면 오류
        if not email or not pdfFile:
            return Response({'error': 'Email and PDF file are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 고유한 파일 이름 생성
            file_name = f'{uuid.uuid4()}.pdf'

            # Document 객체 생성
            document = Document(email=email)

            # Document의 pdfUrl 필드에 upload_to 속성이 걸려있기 때문에 바로 ContentFile 형태로 저장해도 url로 저장됨
            # 이게 가능한 이유는 settings.py에서 default_file_storage로 s3를 지정해놨기때문!!
            document.pdfUrl.save(file_name, ContentFile(pdfFile.read()))

            # Document 객체 저장
            document.save()

            # 테스트를 위해 응답으로 pdfUrl을 추가로 지정했음. api 연동할 땐 documentId만!
            return Response({
                'message': 'File uploaded successfully',
                'pdfUrl': document.pdfUrl.url,
                'documentId': document.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentRead(APIView):
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

class DocumentChange(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description='Modifying a document by uploading a new PDF file',
        manual_parameters=[
            openapi.Parameter(
                'documentId',
                openapi.IN_PATH,
                description="ID of the Document",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'pdfFile',
                openapi.IN_FORM,
                description="PDF File",
                type=openapi.TYPE_FILE
            )
        ],
        responses={
            200: openapi.Response('Document modified successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'pdfUrl': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the updated PDF file')
                }
            )),
            400: 'Bad request. Missing document ID or PDF file.',
            404: 'Document not found.'
        }
    )
    def put(self, request, documentId):
        if not documentId:
            return Response({'error': 'Document ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        document = get_object_or_404(Document, pk=documentId)

        # 클라이언트로부터 전송된 파일을 가져오기
        uploaded_file = request.FILES.get('pdfFile')
        if not uploaded_file:
            return Response({'error': 'No PDF file was uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        s3 = boto3.client('s3')
        bucket_name = 'lawbotttt'
        # 기존 pdfUrl에서 파일 경로를 추출
        pdf_key = document.pdfUrl.name

        # pdf_key에 중복되는 'documents/'를 제거
        if pdf_key.startswith('documents/documents/'):
            pdf_key = pdf_key.replace('documents/documents/', 'documents/', 1)

        try:
            # S3에 새로운 파일 업로드
            s3.put_object(Bucket=bucket_name, Key=pdf_key, Body=uploaded_file.read(), ContentType='application/pdf')
        except Exception as e:
            return Response({'error': 'Failed to upload new PDF file to S3.', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # pdfUrl을 포함한 응답 데이터를 생성하고, 클라이언트에게 반환
        response_data = {
            'pdfUrl': f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{pdf_key}"  # S3 URL 형식에 맞게 수정
        }
        return Response(response_data, status=status.HTTP_200_OK)