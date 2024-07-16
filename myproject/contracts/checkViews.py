import fitz
from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from requests import HTTPError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import ArticleMainSerializer
from .utils.pdfToHtml import pdf_to_html_with_pdfco
from .models import Contract, Type
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

            # S3 url 가져오기
            pdf_url = contract.origin_url.url

            # pdf -> html 코드 변환
            pdfco_api_key = os.getenv('PDFCO_API_KEY')
            try:
                html_content = pdf_to_html_with_pdfco(pdfco_api_key, pdf_url)
            except HTTPError as http_err:
                return Response({'error': f'HTTP error occurred: {str(http_err)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as err:
                return Response({'error': f'Other error occurred: {str(err)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # html 코드 S3에 업로드
            if html_content:
                html_file_name = f'{uuid.uuid4()}.html'

                contract.origin.save(html_file_name, ContentFile(html_content.encode('utf-8')))
                contract.save()
                print(contract.origin.url)

            return Response({
                # 'message': 'success upload files',
                'contractId': contract.id,
                # 'category': contract.category,
                # 'pdf_url': contract.origin_url.url,
                # 'html_url': contract.origin.url,
                # 'extracted_text': uploaded_html_content,
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
                        'contractId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the Contract'),
                        'contract': openapi.Schema(type=openapi.TYPE_STRING, description='Contract HTML Code File'),
                        'articles': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT,
                                        properties={
                                            'articleId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the Article'),
                                            'sentence': openapi.Schema(type=openapi.TYPE_STRING, description='강조할 내용'),
                                            'types': openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(type=openapi.TYPE_STRING),
                                                description=' main(주요조항) | toxin(독소조항) | ambi(모호한 표현)',
                                                ),
                                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='해당 내용이 강조된 근거'),
                                            'law': openapi.Schema(type=openapi.TYPE_STRING, description='해당 내용과 관련있는 법 조항'),
                                            'recommend': openapi.Schema(type=openapi.TYPE_STRING, description='해당 문장의 수정 제안한 내용')
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

            # 텍스트 추출
            html_response = requests.get(html_url)
            html_response.raise_for_status()
            uploaded_html_content = html_response.content.decode('utf-8')

            response = requests.get(pdf_url)
            pdf_content = response.content

            # 페이지 텍스트 추출
            pdf_document = fitz.open(stream=pdf_content, filetype='pdf')
            extracted_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                extracted_text += page.get_text()

            raw_result = analyze_contract(extracted_text)

            # 검토 결과 JSON 형태로 변경
            parsed_result = json.loads(raw_result)
            articles = []
            for i in range(len(parsed_result)):
                article_data = {
                    "contract_id": contract.id,
                    "sentence": parsed_result[i].get("sentence", ""),
                    "description": parsed_result[i].get("description", ""),
                    "law": parsed_result[i].get("law", ""),
                }
                # 시리얼라이저를 이용해 데이터 저장
                serializer = ArticleMainSerializer(data=article_data)

                if serializer.is_valid():
                    article_instance = serializer.save()

                    type_instance = Type.objects.get(name="main")
                    article_instance.type.add(type_instance)

                    article_data = {
                        "articleId": article_instance.id,
                        "sentence": article_instance.sentence,
                        "description": article_instance.description,
                        "law": article_instance.law,
                        "recommend": article_instance.recommend
                    }
                    articles.append(article_data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'contractId': contract.id,
                'contract': uploaded_html_content,
                'type': contract.type,
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