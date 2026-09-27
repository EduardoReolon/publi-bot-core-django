from django.urls import include, path

urlpatterns = [path("api/v1/", include("publibot_core.urls"))]
