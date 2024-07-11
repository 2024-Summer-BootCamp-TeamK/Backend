import fitz
from celery import chain
from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .tasks import contract_origin_save, html_extract_content, pdf_to_text_and_openai, pdf_to_html_task
from .utils.pdfToHtml import pdf_to_html_with_pdfco
from .models import Contract
import uuid
import os
import json


class UploadView(APIView):
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

        try:
            contract = Contract(category=category)
            contract.save()

            file_name = f'{uuid.uuid4()}.pdf'

            result = chain(
                contract_origin_save.s(contract.id, file_name, pdf_file.read()),
                pdf_to_html_task.s(),
            ).apply_async()

            return Response({
                'contractId': contract.id,
                'taskId': result.id
            }, status=status.HTTP_201_CREATED)

        except UnicodeDecodeError as e:
            return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractDetailView(APIView):
    @swagger_auto_schema(
        operation_description='Get the results of reviewing the Contract',
        manual_parameters=[
            openapi.Parameter('contractId',
                              openapi.IN_PATH,
                              description="ID of the Contract",
                              type=openapi.TYPE_INTEGER,
                              required=True),
        ],
        responses={
            200: openapi.Response('Success the results of reviewing the Contract',
                                  openapi.Schema(
                                      type=openapi.TYPE_OBJECT,
                                      properties={
                                          'contractId': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                                       description='ID of the Contract'),
                                          'contract': openapi.Schema(type=openapi.TYPE_STRING,
                                                                     description='Contract HTML Code File'),
                                          'articles': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                     items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                                                                          properties={
                                                                                              'articleId': openapi.Schema(
                                                                                                  type=openapi.TYPE_INTEGER,
                                                                                                  description='ID of the Article'),
                                                                                              'sentence': openapi.Schema(
                                                                                                  type=openapi.TYPE_STRING,
                                                                                                  description='강조할 내용'),
                                                                                              'types': openapi.Schema(
                                                                                                  type=openapi.TYPE_ARRAY,
                                                                                                  items=openapi.Schema(
                                                                                                      type=openapi.TYPE_STRING),
                                                                                                  description=' main(주요조항) | toxin(독소조항) | ambi(모호한 표현)',
                                                                                              ),
                                                                                              'description': openapi.Schema(
                                                                                                  type=openapi.TYPE_STRING,
                                                                                                  description='해당 내용이 강조된 근거'),
                                                                                              'law': openapi.Schema(
                                                                                                  type=openapi.TYPE_STRING,
                                                                                                  description='해당 내용과 관련있는 법 조항'),
                                                                                              'recommend': openapi.Schema(
                                                                                                  type=openapi.TYPE_STRING,
                                                                                                  description='해당 문장의 수정 제안한 내용')
                                                                                          }
                                                                                          ))}
                                  )),
            400: 'Invalid data with Error GPT Request(Article)',
            404: 'Contract Of PDF File does not exist OR Contract Of HTML File does not exist ',
            500: 'Error processing request '
        }
    )
    def get(self, request, contractId):
        try:
            # contractId로 계약서 인스턴스 생성
            contract = Contract.objects.get(id=contractId)

            pdf_url = contract.origin_url.url
            html_url = contract.origin.url

            # 텍스트 추출 (celery)
            uploaded_html_content = html_extract_content(html_url).get()

            articles = pdf_to_text_and_openai(contract.id, pdf_url).get()

            return Response({
                'contractId': contract.id,
                'contract': uploaded_html_content,
                'articles': articles
            }, status=status.HTTP_200_OK)

        except Contract.DoesNotExist:
            return Response({'error': 'Contract does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError as e:
            return Response({'error': 'Error fetching the file: ' + str(e)}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError as e:
            return Response({'error': 'Error decoding JSON: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
