from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm


def home(request):
    return render(request, 'accounts_app/home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts_app/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin_role:
        return redirect('admin_dashboard')
    elif user.is_motorpool:
        return redirect('motorpool_dashboard')
    else:
        return redirect('department_dashboard')