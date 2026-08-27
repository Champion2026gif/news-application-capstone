from django.urls import path

from . import views

app_name = "articles"

urlpatterns = [
    path("", views.ArticleListView.as_view(), name="article_list"),
    path("new/", views.create_article, name="article_create"),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name="article_detail"),

    path("pending/", views.PendingArticleListView.as_view(), name="pending_list"),
    path("<int:pk>/approve/", views.approve_article, name="approve_article"),
    path("<int:pk>/reject/", views.reject_article, name="reject_article"),

    path("newsletters/", views.NewsletterListView.as_view(), name="newsletter_list"),
    path("newsletters/new/", views.create_newsletter, name="newsletter_create"),
    path("newsletters/<int:pk>/", views.NewsletterDetailView.as_view(), name="newsletter_detail"),
]
