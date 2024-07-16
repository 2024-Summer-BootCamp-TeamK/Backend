import fitz
from celery.result import AsyncResult
from django.core.files.base import ContentFile
from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import ArticleMainSerializer
from .tasks import type_save_task, pdf_to_html_task, review_get_task
from .models import Contract
import uuid
import requests
import os
import json
from .utils.openAICall import analyze_contract


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

            file_name = f'{uuid.uuid4()}.pdf'

            # pdf 파일 S3에 업로드
            contract.origin_url.save(file_name, ContentFile(pdf_file.read()))
            contract.save()

            pdf_to_html_task(contract)

            return Response({
                'contractId': contract.id,
            }, status=status.HTTP_201_CREATED)

        except UnicodeDecodeError as e:
            return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        task_id = review_get_task.apply(args=[contractId])
        return Response({'task_id': task_id.id}, status=status.HTTP_200_OK)


def task_status(request, task_id):
    task = AsyncResult(task_id)
    result = {
        'task_id': task_id,
        'status': task.status,
        'result': task.result,
    }
    return Response(result, status=status.HTTP_200_OK)
