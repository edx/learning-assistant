# Generated by Django 3.2.20 on 2023-08-24 14:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning_assistant', '0003_courseprompt_json_prompt_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courseprompt',
            name='prompt',
        ),
    ]
