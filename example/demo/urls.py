from django.urls import path

from . import views

urlpatterns = views.routes.get_urlpatterns()

urlpatterns += [
    path("3/", views.api_3),
]
