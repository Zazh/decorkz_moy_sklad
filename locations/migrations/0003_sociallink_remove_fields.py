from django.db import migrations, models
import django.db.models.deletion


def populate_socials(apps, schema_editor):
    CompanyInfo = apps.get_model('locations', 'CompanyInfo')
    SocialLink = apps.get_model('locations', 'SocialLink')

    info = CompanyInfo.objects.first()
    if not info:
        return

    SocialLink.objects.create(
        company=info,
        name='2ГИС',
        url='https://go.2gis.com/EPITb',
        svg_icon='<svg class="h-8 md:h-9" clip-rule="evenodd" fill-rule="evenodd" image-rendering="optimizeQuality" shape-rendering="geometricPrecision" text-rendering="geometricPrecision" viewBox="0 0 11216.09 4775.7" xmlns="http://www.w3.org/2000/svg"><g fill-rule="nonzero"><path d="M4775.84 2387.87c0-293.75-55.66-573.93-152.69-833.81-25.67 855.4-895.11 1517.68-1405.56 1955.95h1277.69c178.6-334.64 280.56-716.41 280.56-1122.14zM3852.17 504.36C3447.63 189.4 2940.41 0 2387.97 0 1069.14 0 0 1069.14 0 2387.87 0 3706.59 1069.14 4775.7 2387.97 4775.7c603.91 0 1153.8-225.95 1574.32-595.72H2233.48l-5.27-507.69c1041.67-905.55 1680.23-1517.96 1680.23-2109.49 0-219.84-83.74-497.26-460.58-497.26-298.4 0-586.26 172.85-533.94 895.11h-607.14C2154.95 1123.23 2610.35 458.4 3479.18 458.4c134.7 0 259.3 16.08 372.99 45.96z" fill="currentColor"/><path d="M6990.65 1650.41h564.82c19.31-429.6-125.46-1110.38-1057.15-1110.38-685.57 0-1182.83 410.43-1182.83 1264.87 0 115.87 4.79 714.47 4.79 1086.18 0 926.99 642.16 1129.69 1182.84 1129.69 323.46 0 791.72-72.45 1008.93-308.98V2234.54H6449.98v535.88h473.15v651.74c-357.29 120.66-1009.03 168.97-1009.03-651.74V1804.9c0-574.5 265.56-772.41 559.98-772.41 304.19 0 516.57 154.49 516.57 617.92zm4201.34 1433.74c24.1-1322.67-1491.68-883.44-1477.3-1622.02 4.8-260.63 173.8-429.64 449.05-429.64 294.46 0 468.13 173.8 463.33 627.64h555.19c14.52-410.42-82.03-1110.38-999.21-1110.38-569.7 0-1037.93 280.05-1047.65 902.76-24.11 1269.56 1501.4 854.44 1477.29 1622.05-9.72 313.77-236.66 453.74-492.46 453.74-299.26 0-540.68-173.79-492.37-695.16h-560.12c-62.72 690.37 241.46 1182.84 1047.69 1182.84 680.65 0 1066.83-376.64 1076.56-931.83zm-2550.38 888.27h-569.57V593.17h569.57zm0 0h-569.57V593.17h569.57z" fill="currentColor"/></g></svg>',
        sort_order=0,
    )
    SocialLink.objects.create(
        company=info,
        name='WhatsApp',
        url='https://api.whatsapp.com/send/?phone=77714028897&text=Здравствуйте!',
        svg_icon='<svg class="h-8 md:h-9" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><g transform="translate(-300.000000, -7599.000000)" fill="currentColor"><g transform="translate(56.000000, 160.000000)"><path d="M259.821,7453.12124 C259.58,7453.80344 258.622,7454.36761 257.858,7454.53266 C257.335,7454.64369 256.653,7454.73172 254.355,7453.77943 C251.774,7452.71011 248.19,7448.90097 248.19,7446.36621 C248.19,7445.07582 248.934,7443.57337 250.235,7443.57337 C250.861,7443.57337 250.999,7443.58538 251.205,7444.07952 C251.446,7444.6617 252.034,7446.09613 252.104,7446.24317 C252.393,7446.84635 251.81,7447.19946 251.387,7447.72462 C251.252,7447.88266 251.099,7448.05372 251.27,7448.3478 C251.44,7448.63589 252.028,7449.59418 252.892,7450.36341 C254.008,7451.35771 254.913,7451.6748 255.237,7451.80984 C255.478,7451.90987 255.766,7451.88687 255.942,7451.69881 C256.165,7451.45774 256.442,7451.05762 256.724,7450.6635 C256.923,7450.38141 257.176,7450.3464 257.441,7450.44643 C257.62,7450.50845 259.895,7451.56477 259.991,7451.73382 C260.062,7451.85686 260.062,7452.43903 259.821,7453.12124 M254.002,7439 L253.997,7439 L253.997,7439 C248.484,7439 244,7443.48535 244,7449 C244,7451.18666 244.705,7453.21526 245.904,7454.86076 L244.658,7458.57687 L248.501,7457.3485 C250.082,7458.39482 251.969,7459 254.002,7459 C259.515,7459 264,7454.51465 264,7449 C264,7443.48535 259.515,7439 254.002,7439"/></g></g></g></svg>',
        sort_order=1,
    )
    SocialLink.objects.create(
        company=info,
        name='Instagram',
        url='https://www.instagram.com/decor_kz_company',
        svg_icon='<svg class="h-8 md:h-9" viewBox="0 0 24 24" fill="currentColor"><path d="M16.19 2H7.81C4.17 2 2 4.17 2 7.81V16.18C2 19.83 4.17 22 7.81 22H16.18C19.82 22 21.99 19.83 21.99 16.19V7.81C22 4.17 19.83 2 16.19 2ZM12 15.88C9.86 15.88 8.12 14.14 8.12 12C8.12 9.86 9.86 8.12 12 8.12C14.14 8.12 15.88 9.86 15.88 12C15.88 14.14 14.14 15.88 12 15.88ZM17.92 6.88C17.87 7 17.8 7.11 17.71 7.21C17.61 7.3 17.5 7.37 17.38 7.42C17.26 7.47 17.13 7.5 17 7.5C16.73 7.5 16.48 7.4 16.29 7.21C16.2 7.11 16.13 7 16.08 6.88C16.03 6.76 16 6.63 16 6.5C16 6.37 16.03 6.24 16.08 6.12C16.13 5.99 16.2 5.89 16.29 5.79C16.52 5.56 16.87 5.45 17.19 5.52C17.26 5.53 17.32 5.55 17.38 5.58C17.44 5.6 17.5 5.63 17.56 5.67C17.61 5.7 17.66 5.75 17.71 5.79C17.8 5.89 17.87 5.99 17.92 6.12C17.97 6.24 18 6.37 18 6.5C18 6.63 17.97 6.76 17.92 6.88Z"/></svg>',
        sort_order=2,
    )


def reverse_socials(apps, schema_editor):
    SocialLink = apps.get_model('locations', 'SocialLink')
    SocialLink.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0002_populate_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('url', models.URLField(verbose_name='Ссылка')),
                ('svg_icon', models.TextField(verbose_name='SVG иконка')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='socials', to='locations.companyinfo')),
            ],
            options={
                'verbose_name': 'Социальная сеть',
                'verbose_name_plural': 'Социальные сети',
                'ordering': ['sort_order'],
            },
        ),
        migrations.RemoveField(model_name='companyinfo', name='instagram'),
        migrations.RemoveField(model_name='companyinfo', name='whatsapp'),
        migrations.RunPython(populate_socials, reverse_socials),
    ]
