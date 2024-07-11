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

from .utils.modifySentence import replaceStringFromPdf
from .utils.pdfToHtml import pdf_to_html_with_pdfco

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

            self.modify_pdf2pdf(contract, article_ids)
            self.upload_modified_html(contract)

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
    def upload_modified_html(contract):
        try:
            modified_pdf_url = contract.result_url.url
            logger.debug("Modified PDF URL: %s", modified_pdf_url)
            html_content = pdf_to_html_with_pdfco(PDFCO_API_KEY, modified_pdf_url)

            if html_content:
                html_file_name = f'{uuid.uuid4()}.html'
                contract.result.save(html_file_name, ContentFile(html_content.encode('utf-8')))
                contract.save()

        except HTTPError as http_err:
            logger.error("HTTP Error: %s", str(http_err))
            return Response({'error': f'HTTP error occurred: {str(http_err)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            logger.error("Error: %s", str(err))
            return Response({'error': f'Other error occurred: {str(err)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def modify_pdf2pdf(contract, article_ids):
        try:
            origin_pdf_url = contract.origin_url
            logger.debug("Origin PDF URL: %s", origin_pdf_url)
            search_strings, replace_strings = [], []

            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                if article:
                    search_strings.append(article.sentence)
                    replace_strings.append(article.recommend)

            logger.debug("Search Strings: %s", search_strings)
            logger.debug("Replace Strings: %s", replace_strings)

            modified_pdf = replaceStringFromPdf(PDFCO_API_KEY, origin_pdf_url, search_strings, replace_strings)
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




