# your_app_name/migrations/0004_auto_add_initial_data.py
from django.db import migrations

def add_initial_types(apps, schema_editor):
    Type = apps.get_model('contracts', 'Type')
    Type.objects.create(id=1, name='main')
    Type.objects.create(id=2, name='toxin')
    Type.objects.create(id=3, name='ambi')

class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0003_alter_article_law'),
    ]

    operations = [
        migrations.RunPython(add_initial_types),
    ]
