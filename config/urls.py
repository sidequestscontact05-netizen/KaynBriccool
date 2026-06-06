from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def home_view(request):
    if request.method == 'POST':
        return redirect('home')
    if request.user.is_authenticated:
        if request.user.is_admin():
            return redirect('admin_sidequest:dashboard')
        if request.user.acting_as_tasker():
            return redirect('tasks:tasker_dashboard')
        if request.user.acting_as_client():
            return redirect('tasks:client_dashboard')
        if request.user.role == 'both':
            return redirect('tasks:tasker_dashboard')
        return redirect('tasks:client_dashboard')
    from django.views.generic import TemplateView
    return TemplateView.as_view(template_name='home.html')(request)


urlpatterns = [
    path('', home_view, name='home'),
    path('admin-django/', admin.site.urls),
    path('admin-panel/', include('apps.accounts.admin_urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.tasks.urls')),
    path('', include('apps.messaging.urls')),
    path('', include('apps.reputation.urls')),
    path('badges/', include('apps.badges.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
