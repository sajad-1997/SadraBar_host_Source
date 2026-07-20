import threading

# Thread-safe local storage برای نگهداری کاربر
_user_holder = threading.local()


def set_current_user(user):
    _user_holder.user = user


def get_current_user():
    return getattr(_user_holder, "user", None)


class CurrentUserMiddleware:
    """Middleware برای ثبت خودکار کاربر فعال در سیستم"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ذخیره کاربر واردشده
        if request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)

        response = self.get_response(request)

        # پاک کردن بعد از پایان request
        set_current_user(None)

        return response
