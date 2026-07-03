from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.tasks.models import Category, SubCategory


def admin_required(view_func):
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin():
            messages.error(request, _('Accès réservé aux administrateurs.'))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapper


@admin_required
def admin_categories(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'admin_KaynBricool/categories.html', {
        'categories': categories,
    })


@admin_required
def admin_create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug', '').strip()
        if not slug and name:
            slug = slugify(name)
        icon = request.POST.get('icon', 'folder')
        if name and slug:
            if Category.objects.filter(slug=slug).exists():
                messages.error(request, _('Ce slug existe déjà. Choisis-en un autre.'))
                return render(request, 'admin_KaynBricool/category_form.html', {
                    'form_action': 'create',
                    'name': name,
                    'slug': slug,
                    'icon': icon,
                })
            Category.objects.create(name=name, slug=slug, icon=icon)
            messages.success(request, _('Catégorie créée.'))
            return redirect('admin_KaynBricool:categories')
    return render(request, 'admin_KaynBricool/category_form.html', {'form_action': 'create'})


@admin_required
def admin_edit_category(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name')
        slug = request.POST.get('slug', '').strip()
        cat.slug = slug if slug else cat.name.lower().replace(' ', '-')
        cat.icon = request.POST.get('icon')
        cat.save()
        messages.success(request, _('Catégorie modifiée.'))
        return redirect('admin_KaynBricool:categories')
    return render(request, 'admin_KaynBricool/category_form.html', {'cat': cat, 'form_action': 'edit'})


@admin_required
def admin_delete_category(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, _('Catégorie supprimée.'))
        return redirect('admin_KaynBricool:categories')
    return render(request, 'admin_KaynBricool/confirm_delete.html', {
        'item': cat,
        'return_url': 'admin_KaynBricool:categories',
    })


@admin_required
def admin_subcategories(request):
    subs = SubCategory.objects.select_related('category').all().order_by('category', 'name')
    categories = Category.objects.all()
    return render(request, 'admin_KaynBricool/subcategories.html', {
        'subcategories': subs,
    })


@admin_required
def admin_create_subcategory(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        cat_id = request.POST.get('category')
        name = request.POST.get('name')
        slug = request.POST.get('slug', '').strip()
        if not slug and name:
            slug = name.lower().replace(' ', '-')
        if name and cat_id and slug:
            cat = get_object_or_404(Category, id=cat_id)
            SubCategory.objects.create(category=cat, name=name, slug=slug)
            messages.success(request, _('Sous-catégorie créée.'))
            return redirect('admin_KaynBricool:subcategories')
    return render(request, 'admin_KaynBricool/subcategory_form.html', {
        'categories': categories,
        'form_action': 'create',
    })
