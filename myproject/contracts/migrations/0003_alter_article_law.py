# Generated by Django 5.0.6 on 2024-07-10 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0002_type_article_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='law',
            field=models.CharField(max_length=100),
        ),
    ]