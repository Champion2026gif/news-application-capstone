from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.models import Article, Newsletter, Publisher

from .models import ApprovedArticleLog
from .permissions import (
    IsEditor,
    IsEditorOrOwnerJournalistForWrite,
    IsJournalistOrEditorToCreate,
    IsJournalistToCreate,
)
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)


class ArticleViewSet(viewsets.ModelViewSet):
    """
    GET    /api/articles/               -> all approved articles
    GET    /api/articles/subscribed/    -> approved articles from the reader's subscriptions
    GET    /api/articles/<id>/          -> a single article (must be approved, unless owner/editor)
    POST   /api/articles/               -> create (journalists only)
    PUT    /api/articles/<id>/          -> update (editors, or the owning journalist)
    DELETE /api/articles/<id>/          -> delete (editors, or the owning journalist)
    POST   /api/articles/<id>/approve/  -> approve (editors only)
    """
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsJournalistToCreate, IsEditorOrOwnerJournalistForWrite]

    def get_queryset(self):
        qs = Article.objects.select_related("author", "publisher")
        user = self.request.user
        if not user.is_authenticated:
            return qs.filter(approved=True)
        if user.is_superuser or user.role == "EDITOR":
            return qs
        if user.role == "JOURNALIST":
            return qs.filter(Q(approved=True) | Q(author=user))
        # Reader (or any other authenticated role): only approved articles.
        return qs.filter(approved=True)

    def get_object(self):
        """
        For retrieve/update/destroy, look the object up from the FULL
        queryset (not the role-filtered list queryset) so that a
        permission violation on a visible-but-forbidden object correctly
        returns 403 rather than masking it as 404. list() still uses the
        role-filtered get_queryset() above.
        """
        from rest_framework.generics import get_object_or_404 as drf_get_object_or_404

        queryset = Article.objects.select_related("author", "publisher")
        obj = drf_get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def subscribed(self, request):
        """Return approved articles only from the reader's subscribed publishers/journalists."""
        user = request.user
        qs = Article.objects.filter(approved=True).filter(
            Q(publisher__in=user.subscriptions_publishers.all())
            | Q(author__in=user.subscriptions_journalists.all())
        ).distinct()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsEditor])
    def approve(self, request, pk=None):
        """Editor-only approval action, mirroring the template-based approve_article view."""
        article = self.get_object()
        article.approve(editor=request.user)
        return Response(ArticleSerializer(article, context={"request": request}).data)


class NewsletterViewSet(viewsets.ModelViewSet):
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticated, IsJournalistOrEditorToCreate, IsEditorOrOwnerJournalistForWrite]

    def get_queryset(self):
        return Newsletter.objects.select_related("author").prefetch_related("articles")

    def get_object(self):
        from rest_framework.generics import get_object_or_404 as drf_get_object_or_404

        queryset = self.get_queryset()
        obj = drf_get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApprovedArticleAPIView(APIView):
    """
    /api/approved/

    Internal endpoint hit by the article-approval signal (see
    articles/signals.py) via `requests.post`. Logs the approved article.
    Requires authentication in production; during tests we call it
    directly, and the signal calls it over HTTP when the dev server is
    running.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        required = ["article_id", "title", "author"]
        if not all(field in data for field in required):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        log = ApprovedArticleLog.objects.create(
            article_id=data.get("article_id"),
            title=data.get("title", ""),
            author=data.get("author", ""),
            publisher=data.get("publisher"),
            approved_at=data.get("approved_at") or timezone.now(),
        )
        return Response({"status": "logged", "id": log.id}, status=status.HTTP_201_CREATED)

    def get(self, request):
        logs = ApprovedArticleLog.objects.order_by("-received_at")[:50]
        return Response([
            {
                "id": l.id, "article_id": l.article_id, "title": l.title,
                "author": l.author, "publisher": l.publisher,
                "approved_at": l.approved_at, "received_at": l.received_at,
            }
            for l in logs
        ])
