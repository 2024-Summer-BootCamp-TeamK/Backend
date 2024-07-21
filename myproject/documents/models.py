from django.db import models
from .utils.customStorages import CustomS3Boto3Storage

class Document(models.Model):
    pdfUrl = models.FileField(upload_to='documents/', storage=CustomS3Boto3Storage())
    email = models.EmailField()
    password = models.CharField(max_length=255, null=True)
    accessLink = models.CharField(max_length=255, null=True)
    deletedAt = models.DateTimeField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)