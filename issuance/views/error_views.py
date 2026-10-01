from django.shortcuts import render


def csrf_failure(request, reason=""):
    return render(request, "errors/403_csrf.html", status=403)
