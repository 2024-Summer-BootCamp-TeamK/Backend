from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .uploadSerializer import UploadSerializer

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
            201: 'File upload successfully',
            400: 'Invalid data'
        }
    )
    def post(self, request, *args, **kwargs):

        category = request.data.get('category')
        pdf_file = request.FILES.get('pdf_file')

        if not category or not pdf_file:
            return Response({'error': 'Category 나 PDF파일은 필수로 입력해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)


        #pdf파일 S3에 업로드해서 url받고
        # 코드로 s3 업로드 하기
        # 링크 받아와서
        return Response({'message':'success upload files'},status=status.HTTP_200_OK)
