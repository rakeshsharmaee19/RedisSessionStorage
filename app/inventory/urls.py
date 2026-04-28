from django.urls import path

from inventory.views import ProductListAPIView
urlpatterns = [
    path('products/', ProductListAPIView.as_view()),

]
