import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Favorite


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def favorites_page(request):
    from catalog.filters import get_base_queryset
    favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))
    products = get_base_queryset().filter(pk__in=favorite_ids)
    return render(request, 'accounts/favorites.html', {'products': products})


@require_POST
def toggle_favorite(request):
    """Toggle favorite via AJAX. Returns JSON {is_favorite: bool, count: int}."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)

    try:
        data = json.loads(request.body)
        product_id = int(data.get('product_id'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid'}, status=400)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product_id=product_id,
    )

    if not created:
        favorite.delete()

    count = Favorite.objects.filter(user=request.user).count()
    return JsonResponse({'is_favorite': created, 'count': count})


def favorites_preview(request):
    """Return HTML fragment with up to 10 favorite products for mobile panel."""
    if not request.user.is_authenticated:
        return render(request, 'accounts/_favorites_preview.html', {'products': [], 'total': 0})

    from catalog.filters import get_base_queryset
    favorite_qs = Favorite.objects.filter(user=request.user).order_by('-created_at')
    total = favorite_qs.count()
    product_ids = list(favorite_qs[:10].values_list('product_id', flat=True))
    products_qs = get_base_queryset().filter(pk__in=product_ids)
    products_map = {p.pk: p for p in products_qs}
    products = [products_map[pid] for pid in product_ids if pid in products_map]
    return render(request, 'accounts/_favorites_preview.html', {'products': products, 'total': total})


def favorite_ids(request):
    """Return list of favorite product IDs for current user."""
    if not request.user.is_authenticated:
        return JsonResponse({'ids': []})

    ids = list(
        Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
    )
    return JsonResponse({'ids': ids})
