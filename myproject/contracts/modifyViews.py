import logging
import os
import uuid
from django.utils import timezone
from django.core.files.base import ContentFile
from drf_yasg import openapi
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ContractUpdateSerializer, UpdatedContractSerializer
from .models import Contract, Article
from drf_yasg.utils import swagger_auto_schema
from dotenv import load_dotenv
from requests import HTTPError
from .utils.pdfToDocxWithModify import pdf_convert_docx
from .utils.docxToPdf import docx_to_pdf
from .tasks import upload_modified_html_task
load_dotenv()

PDFCO_API_KEY = os.getenv('PDFCO_API_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ContractModifyView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @swagger_auto_schema(
        operation_description="Modify sentences from the origin as desired by the user.",
        request_body=ContractUpdateSerializer(required=False),
    )
    def put(self, request, *args, **kwargs):
        contract_id = kwargs.get('contractId')
        contract = Contract.objects.filter(id=contract_id).first()

        if not contract:
            return Response({'error': '해당 계약서를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ContractUpdateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            article_ids = serializer.validated_data.get('article_ids', [])

            if not article_ids:
                contract.result_url = contract.origin_url
                contract.save()
                return Response(status=status.HTTP_200_OK)

            self.modify_pdf2docx2pdf(contract, article_ids)
            upload_modified_html_task(contract)

            contract.updated_at = timezone.now()
            contract.save()
            return Response(status=status.HTTP_200_OK)

        except ValidationError as ve:
            logger.error("Validation Error: %s", ve.detail)
            return Response({'error': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Exception: %s", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @staticmethod
    def modify_pdf2docx2pdf(contract, article_ids):
        try:
            origin_pdf_url = contract.origin_url
            logger.debug("Origin PDF URL: %s", origin_pdf_url)

            search_replace_list = []  # 튜플 리스트 초기화

            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                if article:
                    search_replace_list.append((article.sentence, article.recommend))  # 튜플을 리스트에 추가

            # 수정사항 적용된 docx파일
            # ex: docx/df2e61b8-13bb-4a01-b7db-b82a3c113bc2.docx
            docx_url = pdf_convert_docx(origin_pdf_url, search_replace_list)

            # docx를 pdf로 변환
            modified_pdf = docx_to_pdf(PDFCO_API_KEY, docx_url)

            if modified_pdf:
                pdf_file_name = f'{uuid.uuid4()}.pdf'
                contract.result_url.save(pdf_file_name, ContentFile(modified_pdf))
                contract.save()

            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                if article:
                    article.revision = True
                    article.save()

        except HTTPError as http_err:
            logger.error("HTTP Error: %s", str(http_err))
            return Response({'error': f'HTTP error occurred: {str(http_err)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error("Error: %s", str(err))
            return Response({'error': f'Other error occurred: {str(err)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class UpdatedContractReadView(APIView):
    @swagger_auto_schema(
        operation_description="수정된 계약서를 조회하는 Url을 반환해주는 API",
        responses={
            200: openapi.Response('Modified Contract retrieved successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'origin_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the Origin PDF file'),
                    'result_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the Modified PDF File')
                }
            )),
            404: 'Contract not found.'
        }
    )
    def get(self, request, *args, **kwargs):
        contract_id = kwargs.get('contractId')
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                serializer = UpdatedContractSerializer(contract)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Contract.DoesNotExist:
                logger.error("Contract not found: %s", contract_id)
                return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error("Exception: %s", str(e))
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error("contractId not provided")
        return Response({'error': 'contractId not provided'}, status=status.HTTP_400_BAD_REQUEST)


class UpdatedContractReadView(APIView):
    @swagger_auto_schema(
        operation_description="수정된 계약서를 조회하는 Url을 반환해주는 API",

        # API 작업의 응답, 문서를 찾은 경우: 200 상태 코드, 못찾은 경우: 404 상태 코드
        responses={
            200: openapi.Response('Modified Contract retrieved successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'origin_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the Origin PDF file'),
                    'result_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL of the Modified PDF File')
                }
            )),
            404: 'Contract not found.'
        }
    )
    def get(self, request, *args, **kwargs):
        contract_id = kwargs.get('contractId')
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
                serializer = UpdatedContractSerializer(contract)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Contract.DoesNotExist:
                return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'error': 'contractId not provided'}, status=status.HTTP_400_BAD_REQUEST)




