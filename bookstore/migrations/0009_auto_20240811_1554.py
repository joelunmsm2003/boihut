# Generated by Django 3.2.11 on 2024-08-11 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookstore', '0008_auto_20240811_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='image2',
            field=models.ImageField(blank=True, upload_to='images/books_img/'),
        ),
        migrations.AlterField(
            model_name='book',
            name='image3',
            field=models.ImageField(blank=True, upload_to='images/books_img/'),
        ),
        migrations.AlterField(
            model_name='book',
            name='image4',
            field=models.ImageField(blank=True, upload_to='images/books_img/'),
        ),
    ]
