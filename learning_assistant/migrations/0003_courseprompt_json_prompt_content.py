# Generated by Django 3.2.20 on 2023-08-24 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_assistant', '0002_alter_courseprompt_prompt'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseprompt',
            name='json_prompt_content',
            field=models.JSONField(null=True),
        ),
    ]