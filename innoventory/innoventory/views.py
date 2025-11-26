from django.shortcuts import render
from accounts.forms import UserEditForm
from products.forms import ThresholdForm
from django.contrib.auth.decorators import login_required

@login_required
def settings_view(request):
    if request.method == 'POST' and 'profile_form_submit' in request.POST:
        profile_form = UserEditForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
    else:
        profile_form = UserEditForm(instance=request.user)

    threshold_form = None
    if request.user.role == 'admin':
        if request.method == 'POST' and 'threshold_form_submit' in request.POST:
            threshold_form = ThresholdForm(request.POST)
            if threshold_form.is_valid():
                threshold_form.save()
        else:
            threshold_form = ThresholdForm()

    context = {
        'profile_form': profile_form,
        'threshold_form': threshold_form
    }

    return render(request, 'innoventory/settings.html', context)
