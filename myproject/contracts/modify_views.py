from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .modify_serializers import ContractUpdateSerializer
from .models import Contract
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


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


class ContractModifyView(APIView):

    @swagger_auto_schema(request_body=ContractUpdateSerializer)
    def put(self, request, *args, **kwargs):

        contract_id = kwargs.get('contractId')
        contract = Contract.objects.filter(id=contract_id).first()

        if contract:  # contract 가 있다면
            contract_origin = contract.origin               # contract_id로 해당 Contract origin 필드 가져옴
            serializer = ContractUpdateSerializer(data=request.data)  # reqeust로 넘어온 data를 serializer로 역직렬화(JSON -> 데이터)

            if serializer.is_valid():  # 유효하다면
                article_ids = serializer.validated_data.get('article_ids', [])

                if not article_ids:   # article_ids가 빈 배열인 경우
                    contract.result_url = contract.origin_url
                    contract.save()
                    return Response({
                        'origin_url': contract.origin_url,
                        'result_url': contract.result_url
                    }, status=status.HTTP_200_OK)

                # 빈 배열이 아닌 경우
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors ,status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': '해당 계약서를 찾을 수 없습니다.'},status=status.HTTP_404_NOT_FOUND)











