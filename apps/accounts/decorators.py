from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


def client_required(view_func):
    @wraps(view_func)
    def _wrapper_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.acting_as_client():
            return view_func(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.acting_as_tasker():
            messages.warning(request, _("Page réservée aux clients. Basculez en mode Client pour y accéder."))
            return redirect('tasks:tasker_dashboard')
        return redirect('home')
    return _wrapper_view


def tasker_required(view_func):
    @wraps(view_func)
    def _wrapper_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.acting_as_tasker():
            return view_func(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.acting_as_client():
            messages.warning(request, _("Page réservée aux taskers. Basculez en mode Tasker pour y accéder."))
            return redirect('tasks:client_dashboard')
        return redirect('home')
    return _wrapper_view
