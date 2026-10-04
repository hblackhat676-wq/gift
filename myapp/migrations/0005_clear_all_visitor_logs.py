from django.db import migrations

def clear_all_visitor_logs(apps, schema_editor):
    VisitorLog = apps.get_model('myapp', 'VisitorLog')
    VisitorLog.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_alter_visitorlog_options_visitorlog_altitude_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_all_visitor_logs, reverse_code=migrations.RunPython.noop),
    ]
