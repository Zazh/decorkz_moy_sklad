from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0004_expand_image_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcard',
            name='images_synced_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Последняя синхр. фото'),
        ),
    ]
