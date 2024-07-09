import os

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from .modify_serializers import ContractUpdateSerializer
from .models import Contract, Article
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from dotenv import load_dotenv
import requests

'''
        수정 시퀀스
        1. contractId와 reqeust를 통해 넘겨받은 articleId의 배열을 이용
        2. contractId에 해당하는 Contract의 origin필드에 들어있는 html코드속
         넘겨받은 배열의 articleId에 해당하는 문장들을 articleId의 recommend필드의 문장으로 각각 수정
        3. 수정된 html코드는 Contractd의 result필드에 들어감
        4. 해당 html코드를 pdf형태로 만들고 S3에 업로드 후 Contract의 result_url필드로 해당 객체의 url 삽입
        5. response로 result_url과 origin_url 반환
            
        issue는
        1,2,3 -> 계약서 수정하기
        4 -> 수정된 계약서 S3 업로드
        5 -> 수정하기 API 구현
'''
load_dotenv()


class ContractModifyView(APIView):

    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="Modify sentences from the origin as desired by the user.",
        request_body=ContractUpdateSerializer,
    )
    def put(self, request, *args, **kwargs):

        contract_id = kwargs.get('contractId')
        contract = Contract.objects.filter(id=contract_id).first()

        if contract:  # contract 가 있다면
            serializer = ContractUpdateSerializer(data=request.data)  # reqeust로 넘어온 data를 serializer로 역직렬화(JSON -> 데이터)

            if serializer.is_valid():  # 유효하다면
                article_ids = serializer.validated_data.get('article_ids', [])

                if not article_ids:   # article_ids가 빈 배열인 경우
                    contract.result_url = contract.origin_url
                    contract.save()
                    return Response(status=status.HTTP_200_OK)
                # 빈 배열이 아닌 경우
                url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/{contract.origin.name}'
                contract_origin_html = self.get_html_from_url(url) # url로 가져온 html 문자열 저장

                modified_html = self.modify_html(contract_origin_html, article_ids) # html 속 선택 조항들 수정 진행




                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors ,status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': '해당 계약서를 찾을 수 없습니다.'},status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_html_from_url(url): # url을 이용해 html파일을 읽어온다
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
            response.encoding = 'utf-8'  # 인코딩 설정
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    @staticmethod
    def modify_html(html, article_ids): # html 수정하는 함수
        try:
            for article_id in article_ids:
                article = Article.objects.filter(id=article_id).first()
                before = article.sentence   # 변경 전 문장
                after = article.recommend   # 변경 후 문장

                if before in html:   # 변경 전 문장을 html에서 탐색
                    html = html.replace(before,after) # 탐색이 되었다면, 해당 문장을 변경 후 문장으로 교체 후 재할당

            return html

        except Article.DoesNotExist:
            message = {"error": f"Article with id {article_id} does not exist."}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            message = {"error": f"An error occurred while processing article: {str(e)}"}
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




















