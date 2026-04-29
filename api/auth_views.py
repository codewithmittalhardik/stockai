from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Try to find user by email
        user = User.objects.filter(email=email).first()
        if user:
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                return redirect('/')
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name', 'User')
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(username=email.split('@')[0], email=email, password=password)
            login(request, user)
            return redirect('/')
        return render(request, 'signup.html', {'error': 'Email already exists'})
    return render(request, 'signup.html')

def logout_view(request):
    logout(request)
    return redirect('/login/')

@login_required(login_url='/login/')
def index_view(request):
    return render(request, 'index.html')
