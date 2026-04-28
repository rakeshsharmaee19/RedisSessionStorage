from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status

from cart import redis_cart
from cart.serializers import *
from rest_framework.views import APIView

from inventory.models import Product


# Create your views here.
class CartView(APIView):
    @extend_schema(
        responses={200: CartItemSerializer(many=True)},
        description="Get all cart items for the current session."
    )
    def get(self, request):
        try:
            session_id = request.session.session_key
            cart_data = redis_cart.get_cart(session_id)
            promo_code = redis_cart.get_cart_promo_code(session_id)
            return JsonResponse({
                "success": True,
                "message": "Successfully get cart data",
                "data": {
                    "items": cart_data,
                    "promo_code": promo_code
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            session_id = request.session.session_key
            redis_cart.clear_cart(session_id)
            return JsonResponse({
                "success": True,
                "message": "Successfully delete cart data",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AddToCartView(APIView):
    @extend_schema(
        request=AddToCartSerializer,
        responses={200: "Product added to card successfully."},
        description="Add a product to the cart"
    )
    def post(self, request):
        try:
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key

            serializer = AddToCartSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.data

            redis_cart.add_to_cart(
                session_id,
                data["product_id"],
                data["quantity"],
                data["name"],
                data["price"])
            return JsonResponse({
                "success": True,
                "message": "Product added to card successfully.",
                "data": data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromCartView(APIView):
    @extend_schema(
        request=RemoveFromCartSerializer,
        responses={200, None},
        description="remove a product from the current cart session."
    )
    def put(self, request):
        try:
            session_id = request.session.session_key

            serializer = RemoveFromCartSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            product_id = request.data["product_id"]

            redis_cart.remove_from_cart(session_id, product_id)

            return JsonResponse({
                "success": True,
                "message": "Product removed from cart successfully.",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateQuantityView(APIView):
    @extend_schema(
        request=UpdateQuantitySerializer,
        responses={200, None},
        description="Update quantity of a product in the cart. Action can be 'inc' and 'dec'."
    )
    def put(self, request):
        try:
            session_id = request.session.session_key
            product_id = request.data.get("product_id")
            action = request.data.get("action", "inc")

            if action == "inc":
                redis_cart.increment_cart(session_id, product_id)
            else:
                redis_cart.decrement_cart(session_id, product_id)

            return JsonResponse({
                "success": True,
                "message": "Cart updated successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SetQuantityView(APIView):
    @extend_schema(
        request=SetQuantitySerializer,
        responses={200, None},
        description="Set quantity of a product in the cart."
    )
    def put(self, request):
        session_id = request.session.session_key

        serializer = SetQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data.get("product_id")
        quantity = serializer.validated_data.get("quantity")

        updated_quantity = redis_cart.set_quantity(session_id, product_id, quantity)

        if not updated_quantity:
            return JsonResponse({
                "success": False,
                "error": str(updated_quantity)
            }, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({
            "success": True,
            "message": "Cart updated successfully.",
        }, status=status.HTTP_200_OK)


class CartPromoView(APIView):
    @extend_schema(
        request=CartPromotionSerializer,
        responses={200, None},
        description="Apply a promo to the cart."
    )

    def post(self, request):
        try:
            session_id = request.session.session_key

            serializer = CartPromotionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            promo_code = serializer.validated_data.get("promo_code")
            redis_cart.set_cart_promo_code(session_id, promo_code)
            return JsonResponse({
                "success": True,
                "message": "Promo applied successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CartCheckoutView(APIView):
    @extend_schema(
        responses={200: CheckoutResponseSerializer(many=True)},
        description="Validate and sanitize the cart before checkout. Removes missing products and updates price/name if needed."
    )
    def post(self, request):
        try:
            session_id = request.session.session_key
            cart_items = redis_cart.get_cart(session_id)

            if not cart_items:
                return JsonResponse({
                    "success": False,
                    "message": "No cart item is present"
                }, status=status.HTTP_400_BAD_REQUEST)

            product_ids = [item["product_id"] for item in cart_items]

            products = Product.objects.filter(id__in=product_ids, is_active=True)
            product_map = {product.id: product for product in products}
            cleaned_cart = []
            for i in cart_items:
                product_id = i["product_id"]
                product = product_map.get(product_id)

                if not product:
                    redis_cart.remove_from_cart(session_id, product_id)
                    continue

                if i["name"] != product.name or float(i["price"]) != float(product.price):
                    redis_cart.update_cart_item(
                        session_id, product_id, product.name, product.price,
                        i["quantity"]
                    )
                    i["name"] = product.name
                    i["price"] = float(product.price)

                i["valid"] = True
                i["error"] = ""
                cleaned_cart.append(i)
            return JsonResponse({
                "success": True,
                "message": "cart data fetched successfully.",
                "data": cleaned_cart
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
