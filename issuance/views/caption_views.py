# 4️⃣ caption_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from ..forms import CaptionForm


@login_required
@never_cache
def add_caption(request):
    form = CaptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('issuance:crud:create_new')
    return render(request, 'issuance/add/add_caption.html', {'form': form})
