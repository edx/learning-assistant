# Generated by Django 4.2.14 on 2024-11-04 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_assistant', '0007_learningassistantmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningassistantmessage',
            name='role',
            field=models.CharField(choices=[('user', 'user'), ('assistant', 'assistant')], max_length=64),
        ),
    ]
