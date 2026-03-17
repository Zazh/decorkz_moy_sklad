from django.shortcuts import render
from .models import Location, CompanyInfo


def points_of_sales(request):
    points = Location.objects.filter(is_active=True)

    city = request.GET.get('city', '')
    point_type = request.GET.get('point_type', '')

    if city:
        points = points.filter(city=city)

    if point_type == 'official':
        points = points.filter(is_official=True)
    elif point_type == 'partner':
        points = points.filter(is_official=False)

    cities_raw = Location.objects.filter(is_active=True).order_by('city').values_list('city', flat=True).distinct()
    city_choices = dict(Location.CITY_CHOICES)
    cities_display = [(c, city_choices.get(c, c)) for c in cities_raw]

    return render(request, 'locations/points_of_sales.html', {
        'points': points,
        'cities': cities_display,
        'selected_city': city,
        'selected_point_type': point_type,
        'og_title': 'Точки продаж — Decorkz.kz',
        'meta_description': 'Точки продаж Decorkz.kz в Алматы и Астане. Адреса магазинов, телефоны и часы работы.',
    })


def contacts(request):
    info = CompanyInfo.objects.prefetch_related('socials').first()
    return render(request, 'locations/contacts.html', {
        'contacts': info,
        'og_title': 'Контакты — Decorkz.kz',
        'meta_description': 'Контактная информация компании Decorkz.kz. Телефон, email, адрес.',
    })
