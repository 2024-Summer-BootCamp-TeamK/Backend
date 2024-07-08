from django.db import models


class Contract(models.Model):
    category = models.CharField(max_length=20)
    origin = models.TextField()
    origin_url = models.CharField(max_length=200, null=True)
    result = models.TextField(null=True)
    result_url = models.CharField(max_length=500, null=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)


class Article(models.Model):
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    sentence = models.CharField(max_length=500)
    description = models.CharField(max_length=500)
    law = models.CharField(max_length=20)
    recommend = models.CharField(max_length=500)
    revision = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

