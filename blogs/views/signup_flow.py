
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.contrib.auth import get_user_model, login

from blogs.models import Blog
from blogs.helpers import is_protected

import pydnsbl
from pydnsbl.providers import Provider

import random
import os


def signup(request):
    title = request.POST.get('title', '')
    subdomain = slugify(request.POST.get('subdomain', '')).replace('_', '-')
    content = request.POST.get('content', '')
    email = request.POST.get('email', '')
    password = request.POST.get('password', '')

    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    error_messages = []

    if request.user.is_authenticated:
        return redirect('account')

    # Check password valid
    if password and len(password) < 6:
        error_messages.append('La contraseña es muy corta')
        password = ''

    # Check subdomain unique
    if subdomain and (Blog.objects.filter(subdomain=subdomain).count() or is_protected(subdomain)):
        error_messages.append('Este subdominio ya fue reclamado')
        subdomain = ''

    # Check email unique and valid
    if email and Blog.objects.filter(user__email__iexact=email).count():
        error_messages.append('Ese correo electrónico ya está registrado')
        email = ''

    # If all fields are present do spam check and create account
    if title and subdomain and content and email and password:
        # Simple honeypot pre-db check
        if honeypot_check(request) or spam_check(title, content, email, ip, request.META['HTTP_USER_AGENT']):
            error_messages.append(random_error_message())
            return render(request, 'signup_flow/step_1.html', {
                'error_messages': error_messages,
                'dodgy': True})

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user:
            error_messages.append('Ese correo electrónico ya está registrado')
        else:
            try:
                user = User.objects.create_user(username=email, email=email, password=password)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
            
                blog = Blog.objects.filter(user=user).first()
                if not blog:
                    blog = Blog.objects.create(title=title, subdomain=subdomain, content=content, user=user)

                # Log in the user
                login(request, user)

                return redirect('dashboard', id=blog.subdomain)
            except IntegrityError:
                error_messages.append('Ese correo electrónico ya está registrado')
                

            

    if title and subdomain and content and (not email or not password):
        return render(request, 'signup_flow/step_2.html', {
            'error_messages': error_messages,
            'title': title,
            'subdomain': subdomain,
            'content': content,
            'email': email,
            'password': password
        })

    return render(request, 'signup_flow/step_1.html', {
        'error_messages': error_messages,
        'title': title,
        'subdomain': subdomain,
        'content': content
    })


def honeypot_check(request):
    if request.POST.get('date'):
        return True
    if request.POST.get('name'):
        return True
    if request.POST.get('email', '').endswith('@cleardex.io'):
        return True

    title = request.POST.get('title', '').lower()
    spam_keywords = ['court records', 'labbia', 'insurance', 'seo', 'gamble', 'gambling', 'crypto', 'marketing', 'bangalore']

    for keyword in spam_keywords:
        if keyword in title:
            return True

    return False


def spam_check(title, content, email, user_ip, user_agent):
    print(f'Spamcheck: {user_ip}')
    checker = pydnsbl.DNSBLIpChecker(providers=[ Provider('all.s5h.net') ])
    result = checker.check(user_ip)
    return result.blacklisted


def random_error_message():
    return 'BOTFAGS NOT ALLOWED'

