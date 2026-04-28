from django.db import models


# Create your models here.
class Category(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.RESTRICT)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=55, unique=True)
    is_active = models.BooleanField(default=False)
    level = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey('Category', null=True, blank=True, related_name='products', on_delete=models.RESTRICT)
    slug = models.SlugField(max_length=55, unique=True)
    description = models.TextField(null=True, blank=True)
    is_digital = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name + self.slug
