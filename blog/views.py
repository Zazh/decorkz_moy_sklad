from django.shortcuts import render, get_object_or_404
from .models import Post


def post_list(request):
    posts = Post.objects.filter(is_active=True)
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'og_title': 'Статьи — Decorkz.kz',
        'meta_description': 'Новости компании Decorkz.kz — статьи о декоре, молдингах и отделочных материалах.',
    })


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_active=True)
    og_image = request.build_absolute_uri(post.image.url) if post.image else ''
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'og_title': f'{post.title} — Блог Decorkz.kz',
        'meta_description': post.description[:150] if post.description else f'Читайте статью «{post.title}» в блоге Decorkz.kz.',
        'og_image': og_image,
    })
