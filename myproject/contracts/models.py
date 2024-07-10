from django.db import models


class Contract(models.Model):
    category = models.CharField(max_length=20)
    origin = models.FileField(upload_to='contracts/html/')
    origin_url = models.FileField(upload_to='contracts/')
    result = models.FileField(upload_to='contracts/html/')
    result_url = models.FileField(upload_to='contracts/')
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

class Type(models.Model):
     name = models.CharField(max_length=10)

class Article(models.Model):
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    sentence = models.CharField(max_length=500)
    description = models.CharField(max_length=500)
    law = models.CharField(max_length=100)
    recommend = models.CharField(max_length=500)
    type = models.ManyToManyField("Type")
    revision = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)
