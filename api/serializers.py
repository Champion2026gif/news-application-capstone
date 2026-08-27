from django.contrib.auth import get_user_model
from django.db import models as db_models
from rest_framework import serializers

from articles.models import Article, Newsletter, Publisher

User = get_user_model()


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "first_name", "last_name"]
        read_only_fields = ["id", "role"]


class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    publisher_name = serializers.CharField(source="publisher.name", read_only=True, default=None)

    class Meta:
        model = Article
        fields = [
            "id", "title", "content", "author", "publisher", "publisher_name",
            "created_at", "updated_at", "approved", "approved_by", "approved_at",
        ]
        read_only_fields = ["id", "author", "approved", "approved_by", "approved_at", "created_at", "updated_at"]

    def validate_publisher(self, value):
        """A journalist may only publish through a publisher they belong to."""
        request = self.context.get("request")
        if value is not None and request is not None:
            user = request.user
            if user.role == "JOURNALIST" and not value.journalists.filter(pk=user.pk).exists():
                raise serializers.ValidationError(
                    "You are not registered as a journalist for this publisher."
                )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["author"] = request.user
        validated_data["approved"] = False
        return super().create(validated_data)


class NewsletterSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    articles = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.filter(approved=True), many=True, required=False
    )

    class Meta:
        model = Newsletter
        fields = ["id", "title", "description", "created_at", "author", "articles"]
        read_only_fields = ["id", "author", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["author"] = request.user
        return super().create(validated_data)
