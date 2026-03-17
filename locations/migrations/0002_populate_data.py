from django.db import migrations


def populate_locations(apps, schema_editor):
    Location = apps.get_model('locations', 'Location')
    CompanyInfo = apps.get_model('locations', 'CompanyInfo')

    # Алматы
    Location.objects.create(
        city='almaty',
        name='Decor kz Сокпакбаева',
        address='ул. Сокпакбаева 71а',
        phones='+77714028897',
        schedule='Пн-Сб: 09:00 - 18:00\nВс: выходной',
        map_url='https://go.2gis.com/EPITb',
        is_official=True,
        sort_order=0,
    )
    Location.objects.create(
        city='almaty',
        name='ТЦ Стройсити',
        address='пр-т Суюнбая 2А, бутик 234',
        phones='+77714028897',
        schedule='Пн-Вс: 10:00 - 19:00',
        is_official=True,
        sort_order=1,
    )
    Location.objects.create(
        city='almaty',
        name='ТК ARMADA',
        address='ул. Северное кольцо 7, бутик 23',
        phones='+77714028897',
        schedule='Пн-Вс: 10:00 - 19:00',
        is_official=True,
        sort_order=2,
    )
    Location.objects.create(
        city='almaty',
        name='Саламат 3',
        address='ул. Шаляпина 23, бутик 75',
        phones='+77714028897',
        schedule='Пн-Вс: 10:00 - 19:00',
        is_official=True,
        sort_order=3,
    )

    # Астана
    Location.objects.create(
        city='astana',
        name='Decor KZ Мәңгілік Ел',
        address='пр-т Мәңгілік Ел 48/1',
        phones='+77714028897',
        schedule='Пн-Сб: 09:00 - 18:00\nВс: выходной',
        is_official=True,
        sort_order=0,
    )
    Location.objects.create(
        city='astana',
        name='Decor kz Жиенкулова',
        address='ул. Жиенкулова 2/1',
        phones='+77714028897',
        schedule='Пн-Сб: 09:00 - 18:00\nВс: выходной',
        is_official=True,
        sort_order=1,
    )

    # Информация о компании
    CompanyInfo.objects.create(
        company_name='ТОО Декор КЗ',
        email='info@decorkz.kz',
        phone='+77714028897',
        address='Казахстан, г. Алматы, ул. Сокпакбаева, 71а',
        map_url='https://go.2gis.com/EPITb',
        instagram='decor_kz_company',
        whatsapp='77714028897',
    )


def reverse_populate(apps, schema_editor):
    Location = apps.get_model('locations', 'Location')
    CompanyInfo = apps.get_model('locations', 'CompanyInfo')
    Location.objects.all().delete()
    CompanyInfo.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_locations, reverse_populate),
    ]
