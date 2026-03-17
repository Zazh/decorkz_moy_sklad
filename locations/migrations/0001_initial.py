from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(choices=[('almaty', 'Алматы'), ('astana', 'Астана')], max_length=50, verbose_name='Город')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('address', models.CharField(max_length=500, verbose_name='Адрес')),
                ('phones', models.TextField(blank=True, help_text='Разделять переносом строки', verbose_name='Телефоны')),
                ('schedule', models.TextField(blank=True, help_text='Разделять переносом строки', verbose_name='График работы')),
                ('map_url', models.URLField(blank=True, verbose_name='Ссылка на карту')),
                ('is_official', models.BooleanField(default=True, verbose_name='Фирменный салон')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Точка продаж',
                'verbose_name_plural': 'Точки продаж',
                'ordering': ['city', 'sort_order'],
            },
        ),
        migrations.CreateModel(
            name='CompanyInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200, verbose_name='Название компании')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('phone', models.CharField(blank=True, max_length=100, verbose_name='Телефон')),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='Адрес')),
                ('map_url', models.URLField(blank=True, verbose_name='Ссылка на карту')),
                ('instagram', models.CharField(blank=True, max_length=200, verbose_name='Instagram')),
                ('whatsapp', models.CharField(blank=True, max_length=100, verbose_name='WhatsApp')),
            ],
            options={
                'verbose_name': 'Информация о компании',
                'verbose_name_plural': 'Информация о компании',
            },
        ),
    ]
