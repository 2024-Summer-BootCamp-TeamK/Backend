from rest_framework import serializers

class UploadSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=100)
    pdf_File = serializers.FileField()
