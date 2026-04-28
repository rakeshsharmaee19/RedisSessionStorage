from django.urls import path

from cart.views import *

urlpatterns = [
    path('add/', AddToCartView.as_view()),
    path('get/', CartView.as_view()),
    path('remove/', RemoveFromCartView.as_view()),
    path('increment/', UpdateQuantityView.as_view()),
    path('set/', SetQuantityView.as_view()),
    path('promo/', CartPromoView.as_view()),
    path('checkout/', CartCheckoutView.as_view()),

]