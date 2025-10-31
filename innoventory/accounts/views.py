from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('register')

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return auth_views.LoginView.as_view(template_name='accounts/login.html')(request)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print("=== REGISTRATION DEBUG ===")
        print("Form data:", request.POST)
        print("Form is valid:", form.is_valid())

        if not form.is_valid():
            print("Form errors:", form.errors.as_json())
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
        else:
            print("Form is valid, attempting to save...")

        if form.is_valid():
            try:
                user = form.save()
                print("=== USER SAVED SUCCESSFULLY ===")
                print(f"User: {user.username}, Email: {user.email}, Phone: {user.phone_number}")
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('login')
            except Exception as e:
                print(f"=== SAVE ERROR: {e} ===")
                messages.error(request, f'Error during registration: {str(e)}')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})