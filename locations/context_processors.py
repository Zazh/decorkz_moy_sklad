from .models import CompanyInfo


def company_socials(request):
    info = CompanyInfo.objects.prefetch_related('socials').first()
    if info:
        return {'footer_socials': info.socials.all()}
    return {'footer_socials': []}
