# Generated manually on 2025-07-01

from django.db import migrations

def convert_boolean_status_to_string(apps, schema_editor):
    OKR = apps.get_model('okrapi', 'OKR')
    
    # Update all active OKRs (True) to 'Active'
    OKR.objects.filter(status='True').update(status='Active')
    
    # Update all inactive OKRs (False) to 'Hold'
    OKR.objects.filter(status='False').update(status='Hold')


class Migration(migrations.Migration):

    dependencies = [
        ('okrapi', '0017_alter_okr_status'),
    ]

    operations = [
        migrations.RunPython(convert_boolean_status_to_string),
    ]
