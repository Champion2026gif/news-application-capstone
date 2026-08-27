from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r"articles", views.ArticleViewSet, basename="article")
router.register(r"newsletters", views.NewsletterViewSet, basename="newsletter")
router.register(r"publishers", views.PublisherViewSet, basename="publisher")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("approved/", views.ApprovedArticleAPIView.as_view(), name="approved_article_log"),
    path("", include(router.urls)),
]
