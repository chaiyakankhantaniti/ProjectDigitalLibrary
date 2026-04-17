from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def librarian_required(view_func):
    """อนุญาตเฉพาะ superuser หรือผู้ใช้ในกลุ่ม Librarian"""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if request.user.groups.filter(name='Librarian').exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้าสำหรับบรรณารักษ์')
        return redirect('index')

    return _wrapped
