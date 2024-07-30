from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'email', 'pdfUrl']

class DocumentUploadSerializer(serializers.Serializer):
    emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="이메일 주소 배열"
    )
    pdfFile = serializers.FileField(
        help_text="PDF 파일"
    )