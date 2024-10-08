# Generated by Django 3.2.11 on 2024-08-08 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookstore', '0002_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='image2',
            field=models.ImageField(default='', upload_to='images/books_img/'),
        ),
        migrations.AddField(
            model_name='book',
            name='image3',
            field=models.ImageField(default='', upload_to='images/books_img/'),
        ),
        migrations.AddField(
            model_name='book',
            name='image4',
            field=models.ImageField(default='', upload_to='images/books_img/'),
        ),
        migrations.AddField(
            model_name='book',
            name='isbn',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
