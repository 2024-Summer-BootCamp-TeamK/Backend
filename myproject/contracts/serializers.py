from rest_framework import serializers
from .models import Contract, Article


class ContractUpdateSerializer(serializers.Serializer):
    article_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,  # 빈 배열도 허용
    )


class UpdatedContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['result_url']


class ArticleMainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['contract_id', 'sentence', 'description', 'law']

class ArticleToxinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['contract_id', 'sentence', 'description', 'law', 'recommend']
