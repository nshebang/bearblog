from django.http import FileResponse
from django.http import HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site
from django.utils import timezone
from django.utils.text import slugify

from blogs.models import Blog, Post, Upvote
from blogs.helpers import get_posts, salt_and_hash, unmark
from blogs.tasks import daily_task
from blogs.views.analytics import render_analytics

import tldextract
import re


def resolve_address(request):
    http_host = request.META['HTTP_HOST']

    if http_host == 'bear-blog.herokuapp.com':
        http_host = request.META.get('HTTP_X_FORWARDED_HOST', 'bear-blog.herokuapp.com')

    sites = Site.objects.all()
    valid_domains = [
        '127.0.0.1:8000',
        '127.0.0.1:8001',
        'localhost:8000',
        'localhost:8001',
        'ichoria.cc',
        'https://ichoria.cc'
    ]

    subdomain_pattern = r'^(?!www\.)((?!www\.)(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(?::\d{1,5})?$'
    regex = re.compile(subdomain_pattern)

    if any(http_host == site for site in valid_domains):
        # Homepage
        return None
    elif regex.match(http_host):
        # Subdomained blog
        return get_object_or_404(Blog, subdomain__iexact=tldextract.extract(http_host).subdomain, user__is_active=True)
    else:
        # Custom domain blog
        return get_blog_with_domain(http_host)


def get_blog_with_domain(domain):
    if not domain:
        return False
    try:
        return Blog.objects.get(domain=domain, user__is_active=True)
    except Blog.DoesNotExist:
        # Handle www subdomain if necessary
        if 'www.' in domain:
            return get_object_or_404(Blog, domain__iexact=domain.replace('www.', ''), user__is_active=True)
        else:
            return get_object_or_404(Blog, domain__iexact=f'www.{domain}', user__is_active=True)


@csrf_exempt
def ping(request):
    domain = request.GET.get("domain", None)
    print(f'Attempting to issue a certificate for {domain}')

    if get_blog_with_domain(domain):
        print('Found correct blog. Issuing certificate.')
        return HttpResponse('Ping', status=200)
    else:
        print(f'Could not find blog with domain {domain}')
        raise Http404('No such blog')


def home(request):
    blog = resolve_address(request)
    if not blog:
        daily_task()
        return render(request, 'landing.html')

    all_posts = blog.posts.filter(publish=True, published_date__lte=timezone.now()).order_by('-published_date')

    meta_description = blog.meta_description or unmark(blog.content)[:157] + '...'

    return render(
        request,
        'home.html',
        {
            'blog': blog,
            'posts': get_posts(all_posts),
            'root': f'https://{blog.subdomain}.ichoria.cc',
            'meta_description': meta_description
        })


def posts(request):
    blog = resolve_address(request)
    if not blog:
        return not_found(request)

    tag = request.GET.get('q', '')

    if tag:
        posts = Post.objects.filter(blog=blog, publish=True, published_date__lte=timezone.now()).order_by('-published_date')
        blog_posts = [post for post in posts if tag in post.tags]
    else:
        all_posts = blog.posts.filter(publish=True, published_date__lte=timezone.now()).order_by('-published_date')
        blog_posts = get_posts(all_posts)

    meta_description = blog.meta_description or unmark(blog.content)[:157] + '...'

    return render(
        request,
        'posts.html',
        {
            'blog': blog,
            'posts': blog_posts,
            'root': f'https://{blog.subdomain}.ichoria.cc',
            'meta_description':  meta_description,
            'query': tag
        }
    )


@csrf_exempt
def post(request, slug):
    blog = resolve_address(request)
    if not blog:
        return not_found(request)
    
     # Check for a custom RSS feed path
    if slug == blog.rss_alias:
        from blogs.views.feed import feed
        return feed(request)

    # Find by post slug
    post = Post.objects.filter(blog=blog, slug__iexact=slugify(slug)).first()
    if not post:
        # Find by post alias
        post = Post.objects.filter(blog=blog, alias__iexact=slug).first()
        if post:
            return redirect('post', slug=post.slug)
        else:
            # Check for a custom blogreel path and render the blog page
            if slug == blog.blog_path or slug == 'blog':
                return posts(request)
            return render(request, '404.html', {'blog': blog}, status=404)
    
    # Check if upvoted
    hash_id = salt_and_hash(request, 'year')
    upvoted = post.upvote_set.filter(hash_id=hash_id).exists()

    root = f'https://{blog.subdomain}.ichoria.cc'
    meta_description = post.meta_description or unmark(post.content)[:157] + '...'
    full_path = f'{root}/{post.slug}/'
    canonical_url = full_path
    if post.canonical_url and post.canonical_url.startswith('https://'):
        canonical_url = post.canonical_url

    if post.publish is False and not request.GET.get('token') == post.token:
        return not_found(request)

    return render(
        request,
        'post.html',
        {
            'blog': blog,
            'content': post.content,
            'post': post,
            'root': f'https:{blog.subdomain}.ichoria.cc',
            'full_path': full_path,
            'canonical_url': canonical_url,
            'meta_description': meta_description,
            'meta_image': post.meta_image or blog.meta_image,
            'upvoted': upvoted
        }
    )


@csrf_exempt
def upvote(request, uid):
    hash_id = salt_and_hash(request, 'year')

    if uid == request.POST.get("uid", "") and not request.POST.get("title", False):
        post = get_object_or_404(Post, uid=uid)
        print("Upvoting", post)
        try:
            upvote, created = Upvote.objects.get_or_create(post=post, hash_id=hash_id)
        
            if created:
                return HttpResponse(f'Upvoted {post.title}')
            raise Http404('Duplicate upvote')
        except Upvote.MultipleObjectsReturned:
            return HttpResponse(f'Upvoted {post.title}')
    raise Http404("Someone's doing something dodgy ʕ •`ᴥ•´ʔ")


def public_analytics(request):
    blog = resolve_address(request)
    if not blog:
        return not_found(request)

    if not blog or not blog.user.settings.upgraded or not blog.public_analytics:
        return not_found(request)

    return render_analytics(request, blog, True)


def not_found(request, *args, **kwargs):
    return render(request, '404.html', status=404)


def sitemap(request):
    blog = resolve_address(request)
    posts = []
    try:
        posts = blog.posts.filter(publish=True, published_date__lte=timezone.now()).order_by('-published_date')
    except AttributeError:
        posts = []

    return render(request, 'sitemap.xml', {'blog': blog, 'posts': posts}, content_type='text/xml')


def robots(request):
    blog = resolve_address(request)
    return render(request, 'robots.txt',  {'blog': blog}, content_type="text/plain")
