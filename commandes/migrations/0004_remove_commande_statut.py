from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0003_add_date_depart_camions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commande',
            name='statut',
        ),
    ]
