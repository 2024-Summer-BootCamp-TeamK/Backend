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


class ContractModifyView(APIView):

    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @swagger_auto_schema(
        operation_description="Modify sentences from the origin as desired by the user.",
        request_body=ContractUpdateSerializer(required=False),
    )
    def put(self, request, *args, **kwargs):
        contract_id = kwargs.get('contractId')
        contract = Contract.objects.filter(id=contract_id).first()

        if contract:  # contract 가 있다면
            serializer = ContractUpdateSerializer(data=request.data)  # reqeust로 넘어온 data를 serializer로 역직렬화(JSON -> 데이터)

            try:
                serializer.is_valid(raise_exception=True)
                article_ids = serializer.validated_data.get('article_ids', [])

                if not article_ids:
                    # article_ids가 빈 배열인 경우 origin_url을 result_url에 복사
                    contract.result_url = contract.origin_url
                    contract.save()
                    return Response(status=status.HTTP_200_OK)

                # 빈 배열이 아닌 경우
                # url로 가져온 html 문자열 저장
                # url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/{contract.origin.name}'
                # contract_origin_html = self.get_html_from_url(url)

                # # html 속 선택 조항들 수정 진행
                # modified_html = self.modify_html(contract_origin_html, article_ids)
                #
                # # 수정본 html 문자열 -> html파일로 -> pdf파일로 -> html,pdf 둘 다 업로드
                # self.upload_html_pdf_to_s3(modified_html, contract)

                # contract 넘겨주면 그냥 pdf경로로 직접 가져와서 수정한다음 pdf S3 업로드까지 한 함수로 진행
                self.modify_pdf2pdf(contract, article_ids)

                # 저장한 수정계약서 pdf를 html로 변환해 S3 업로드
                self.upload_modified_html(contract)

                # 현재 시간으로 업데이트
                contract.updated_at = timezone.now()
                contract.save()
                return Response(status=status.HTTP_200_OK)

            except ValidationError as ve:
                return Response({'error': ve.detail}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'error': '해당 계약서를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

    # @staticmethod
    # def get_html_from_url(url): # url을 이용해 html파일을 읽어온다
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
    #         response.encoding = 'utf-8'  # 인코딩 설정
    #         return response.text
    #     except requests.exceptions.RequestException as e:
    #         print(f"Error fetching URL: {e}")
    #         return None

    @staticmethod
    def upload_modified_html(contract):
        try:
            # 수정된 계약서 url 가져오기
            modified_pdf_url = contract.result_url.url

            # pdf -> html 코드 변환
            # pdf -> html 코드 변환
            pdfco_api_key = os.getenv('PDFCO_API_KEY')
            try:
                html_content = pdf_to_html_with_pdfco(pdfco_api_key, modified_pdf_url)
            except HTTPError as http_err:
                return Response({'error': f'HTTP error occurred: {str(http_err)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as err:
                return Response({'error': f'Other error occurred: {str(err)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # html 코드 S3에 업로드
            if html_content:
                html_file_name = f'{uuid.uuid4()}.html'

                contract.result.save(html_file_name, ContentFile(html_content.encode('utf-8')))
                contract.save()
                print(contract.result.url)
            return None

        except UnicodeDecodeError as e:
            return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def modify_pdf2pdf(contract, article_ids):
        try:
            origin_pdf_url = contract.origin_url

            # 기존 리스트 초기화
            search_strings = []
            replace_strings = []

            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                if article:  # article이 None이 아닌 경우에만 처리
                    search_strings.append(article.sentence)  # 변경 전 문장 추가
                    replace_strings.append(article.recommend)  # 변경 후 문장 추가

            pdfco_api_key = os.environ.get('PDFCO_API_KEY')
            modified_pdf = replaceStringFromPdf(pdfco_api_key, origin_pdf_url, search_strings, replace_strings)
            if modified_pdf:
                pdf_file_name = f'{uuid.uuid4()}.pdf'

                contract.result_url.save(pdf_file_name, ContentFile(modified_pdf))
                print(contract.result_url)
                contract.save()

            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                article.revision = True  # 수정여부 True로 변경
                article.save()

            return None

        except UnicodeDecodeError as e:
            return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #
    # @staticmethod
    # def modify_html(html, article_ids): # html 수정하는 함수
    #     try:
    #         for article_id in article_ids:
    #             article = Article.objects.filter(id=article_id).first()
    #             before = article.sentence   # 변경 전 문장
    #             after = article.recommend   # 변경 후 문장
    #
    #             if before in html:   # 변경 전 문장을 html에서 탐색
    #                 html = replace_and_generate_html(html,before,after) # 탐색이 되었다면, 해당 문장을 변경 후 문장으로 교체 후 재할당
    #             article.revision = True # 수정여부 True로 변경
    #             article.save()
    #         return html
    #
    #     except Article.DoesNotExist:
    #         message = {"error": f"Article with id {article_id} does not exist."}
    #         return Response(message, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         message = {"error": f"An error occurred while processing article: {str(e)}"}
    #         return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @staticmethod
    # def upload_html_pdf_to_s3(html_content,contract):  # html이 문자열로 되어있는 것을 html파일로 만듬
    #     try:
    #         file_name = f'{uuid.uuid4()}.html'
    #
    #         contract.result.save(file_name, ContentFile(html_content.encode('utf-8')))
    #         contract.save()
    #
    #         # html 업로드한 url
    #         html_url = contract.result.url
    #
    #         pdfco_api_key = os.environ.get('PDFCO_API_KEY')
    #         pdf_content = html_to_pdf_with_pdfco(pdfco_api_key, html_url)
    #         if pdf_content:
    #             pdf_file_name = f'{uuid.uuid4()}.pdf'
    #
    #             contract.result_url.save(pdf_file_name, ContentFile(pdf_content))
    #             print(contract.result_url)
    #             contract.save()
    #
    #         return None
    #
    #     except UnicodeDecodeError as e:
    #         return Response({'error': 'Unicode decode error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     except Exception as e:
    #         return Response({'error': {e}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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




