from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from dotenv import load_dotenv
from .utils import pdf_to_html_with_pdfco
from .models import Contract
import uuid
import requests
import os


class uploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="Upload a PDF file with a category",
        manual_parameters=[
            openapi.Parameter('category',
                              openapi.IN_FORM,
                              description="Category of the file",
                              type=openapi.TYPE_STRING,
                              required=True),
            openapi.Parameter('pdf_file',
                              openapi.IN_FORM,
                              description="PDF file to upload",
                              type=openapi.TYPE_FILE,
                              required=True),
        ],
        responses={
            201: openapi.Response(
               'File upload successfully',
                 openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'contractId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the Contract'),
                    }
                )
            ),
            400: 'Invalid data'
        }
    )
    def post(self, request, *args, **kwargs):

        category = request.data.get('category')
        pdf_file = request.FILES.get('pdf_file')

        if not category or not pdf_file:
            return Response({'error': 'Category와 PDF파일은 필수로 입력해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try :
            contract = Contract(category=category)

            file_name = f'{uuid.uuid4()}.pdf'

            # pdf 파일 S3에 업로드
            contract.origin_url.save(file_name, ContentFile(pdf_file.read()))
            contract.save()

            # S3 url 가져오기.
            pdf_url = contract.origin_url.url

            # pdf -> html 코드 변환
            pdfco_api_key = os.environ.get('PDFCO_API_KEY')
            html_content = pdf_to_html_with_pdfco(pdfco_api_key, pdf_url)

            # html 코드 S3에 업로드
            if html_content:
                html_file_name = f'{uuid.uuid4()}.html'

                contract.origin.save(html_file_name, ContentFile(html_content.encode('utf-8')))
                contract.save()

                # 텍스트 추출
                # html_url = contract.origin.url
                # html_response = requests.get(html_url)
                # html_response.raise_for_status()
                # uploaded_html_content = html_response.content.decode('utf-8')

            return Response({
                # 'message': 'success upload files',
                'contract_id': contract.id,
                # 'category': contract.category,
                # 'pdf_url': contract.origin_url.url,
                # 'html_url': contract.origin.url,
                # 'extracted_text': uploaded_html_content,
            }, status=status.HTTP_201_CREATED)

        except UnicodeDecodeError as e:
            return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)