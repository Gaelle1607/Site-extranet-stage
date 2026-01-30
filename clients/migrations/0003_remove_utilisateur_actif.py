from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_add_demande_mot_de_passe'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='utilisateur',
            name='actif',
        ),
    ]
