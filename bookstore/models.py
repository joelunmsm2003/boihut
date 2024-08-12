from django.db import models
from category.models import Category
from django.conf import settings



class Book(models.Model):
    STATE_CHOICES = (
      ('New', 'New'),
      ('Used', 'Used'),
      ('Collectible', 'Collectible'),
      ('Refurbished', 'Refurbished'),
      ('Unspecified', 'Unspecified'),
  )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=60)
    image = models.ImageField(upload_to="images/books_img/", blank=True)
    image2 = models.ImageField(upload_to="images/books_img/", blank=True)
    image3 = models.ImageField(upload_to="images/books_img/", blank=True)
    image4 = models.ImageField(upload_to="images/books_img/", blank=True)
    image_google_api = models.CharField(max_length=200,blank=True)
    author = models.CharField(max_length=200,blank=True)
    discount = models.CharField(max_length=200,blank=True)
    editorial = models.CharField(max_length=200,blank=True)
    state = models.CharField(max_length=200, choices=STATE_CHOICES, default='Nuevo')
    isbn = models.CharField(max_length=200,blank=True)
    format = models.CharField(max_length=200,blank=True)
    year = models.CharField(max_length=200,blank=True)
    number_pages = models.CharField(max_length=200,blank=True)
    binding = models.CharField(max_length=200,blank=True)
    dimensions = models.CharField(max_length=200,blank=True)
    description = models.TextField(max_length=3000,blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.IntegerField(blank=False)
    stocks = models.IntegerField(blank=False)
    stocks_available = models.BooleanField(default=True)
    modified_on = models.DateTimeField(auto_now_add=True)
    created_on = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


    def __str__(self):
      return self.title


