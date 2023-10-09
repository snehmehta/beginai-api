from django.urls import path

from text import views

app_name = "text"

urlpatterns = [
    path("v1/models/", views.models, name="models"),
    path("v1/generate/", views.generate, name="generate"),
]