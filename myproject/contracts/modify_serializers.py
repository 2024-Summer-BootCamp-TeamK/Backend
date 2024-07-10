from rest_framework import serializers


class ContractUpdateSerializer(serializers.Serializer):
    article_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,  # 빈 배열도 허용
    )