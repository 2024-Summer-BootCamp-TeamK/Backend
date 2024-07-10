from rest_framework import serializers
from contracts.models import Article, Type


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['contract_id', 'sentence', 'description', 'law', 'recommend']

