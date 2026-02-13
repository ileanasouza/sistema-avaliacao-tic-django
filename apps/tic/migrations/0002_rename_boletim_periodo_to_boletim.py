from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tic", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="atitudesperiodotic",
            old_name="boletim_periodo",
            new_name="boletim",
        ),
    ]



