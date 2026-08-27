from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/reader/", views.reader_dashboard, name="reader_dashboard"),
    path("dashboard/journalist/", views.journalist_dashboard, name="journalist_dashboard"),
    path("dashboard/editor/", views.editor_dashboard, name="editor_dashboard"),
]
