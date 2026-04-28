from rest_framework import serializers


class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price = serializers.FloatField()
    name = serializers.CharField()


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.FloatField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class RemoveFromCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()


class UpdateQuantitySerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=["inc", "dec"], default="inc")


class SetQuantitySerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartPromotionSerializer(serializers.Serializer):
    promo_code = serializers.CharField(max_length=200, min_length=10)


class CheckoutResponseSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.FloatField()
    quantity = serializers.IntegerField()
    valid = serializers.BooleanField()
    error = serializers.CharField(allow_null=True, allow_blank=True)

