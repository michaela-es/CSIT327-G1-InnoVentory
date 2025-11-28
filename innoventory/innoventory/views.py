from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.forms import UserEditForm, ThresholdForm
from sales.models import InventorySettings

@login_required
def settings_view(request):
    profile_form = UserEditForm(instance=request.user)

    if 'profile_form_submit' in request.POST:
        profile_form = UserEditForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            for field, value in profile_form.cleaned_data.items():
                if value not in [None, '']:
                    setattr(request.user, field, value)
            request.user.save()

    threshold_form = None
    if request.user.role == 'admin':
        threshold_settings, _ = InventorySettings.objects.get_or_create(id=1)
        threshold_form = ThresholdForm(instance=threshold_settings)

        if 'threshold_form_submit' in request.POST:
            threshold_form = ThresholdForm(request.POST, instance=threshold_settings)
            if threshold_form.is_valid():
                threshold_form.save()

    context = {
        'profile_form': profile_form,
        'threshold_form': threshold_form
    }

    return render(request, 'settings.html', context)
