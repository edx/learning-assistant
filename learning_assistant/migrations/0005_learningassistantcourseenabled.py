# Generated by Django 3.2.23 on 2024-01-04 15:02

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        ('learning_assistant', '0004_remove_courseprompt_prompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='LearningAssistantCourseEnabled',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255, unique=True)),
                ('enabled', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
