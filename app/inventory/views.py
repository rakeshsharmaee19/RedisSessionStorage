from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from inventory.models import Product
from inventory.serializers import ProductSerializer


# Create your views here.

class ProductListAPIView(APIView):
    def get(self, request):
        try:
            product_objects = Product.objects.all()
            serializer = ProductSerializer(product_objects, many=True)
            return JsonResponse({
                "success": True,
                "message": "Successfully fetched products",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
