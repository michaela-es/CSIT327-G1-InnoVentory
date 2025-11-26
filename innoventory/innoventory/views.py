from django.shortcuts import render
from accounts.forms import UserEditForm
from products.forms import ThresholdForm
from django.contrib.auth.decorators import login_required

@login_required
def settings_view(request):
    profile_form = UserEditForm(request.POST or None, instance=request.user)
    if profile_form.is_valid() and 'profile_form_submit' in request.POST:
        profile_form.save()

    threshold_form = None
    if request.user.role == 'admin':
        threshold_settings, _ = InventorySettings.objects.get_or_create(id=1)
        threshold_form = ThresholdForm(request.POST or None, instance=threshold_settings)

        if threshold_form.is_valid() and 'threshold_form_submit' in request.POST:
            threshold_form.save()

    context = {
        'profile_form': profile_form,
        'threshold_form': threshold_form
    }