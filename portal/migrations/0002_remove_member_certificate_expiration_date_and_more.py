# Generated by Django 5.1.4 on 2025-07-02 08:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='certificate_expiration_date',
        ),
        migrations.RemoveField(
            model_name='member',
            name='enugu_expiring_date',
        ),
        migrations.RemoveField(
            model_name='member',
            name='enugu_issued_date',
        ),
        migrations.RemoveField(
            model_name='member',
            name='member_code',
        ),
        migrations.AddField(
            model_name='member',
            name='certificate_expiry_date',
            field=models.DateField(blank=True, help_text='Certificate expiry date (automatically calculated)', null=True),
        ),
        migrations.AddField(
            model_name='member',
            name='certificate_picture',
            field=models.ImageField(blank=True, null=True, upload_to='certificates/'),
        ),
        migrations.AddField(
            model_name='member',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='member',
            name='certificate_issued_date',
            field=models.DateField(help_text='Date when certificate was issued'),
        ),
        migrations.AlterField(
            model_name='member',
            name='company_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='member',
            name='enugu_first_registration_date',
            field=models.DateField(help_text='Date when first registered in Enugu'),
        ),
        migrations.AlterField(
            model_name='member',
            name='md_phone_number',
            field=models.CharField(max_length=15, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', 'Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')]),
        ),
        migrations.AlterField(
            model_name='member',
            name='md_picture',
            field=models.ImageField(blank=True, null=True, upload_to='md_pictures/'),
        ),
        migrations.AlterField(
            model_name='member',
            name='national_first_registration_date',
            field=models.DateField(help_text='Date when first registered nationally'),
        ),
        migrations.AlterField(
            model_name='member',
            name='rc_number',
            field=models.CharField(help_text='Format: RC123456', max_length=50, validators=[django.core.validators.RegexValidator('^RC\\d+$', 'RC number must start with RC followed by numbers')]),
        ),
    ]
