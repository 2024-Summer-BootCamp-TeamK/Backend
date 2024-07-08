from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
from .models import Document
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class DocumentUploadView(APIView):
    # 파일이나 폼 형태의 데이터를 처리해야하는 경우 필요!
    parser_classes = [MultiPartParser, FormParser]

    # 스웨거에서 파일 업로드를 포함하고싶을 땐 밑에처럼 openapi.IN_FORM으로 스키마 구성하기!!
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
