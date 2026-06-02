from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm
from django.contrib.auth import authenticate, login


def register_view(request):

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            # Password check
            if password != confirm_password:

                return render(
                    request,
                    'accounts/register.html',
                    {
                        'form': form,
                        'error': 'Passwords do not match'
                    }
                )

            # Username check
            if User.objects.filter(username=username).exists():

                return render(
                    request,
                    'accounts/register.html',
                    {
                        'form': form,
                        'error': 'Username already exists'
                    }
                )

            # Create user
            User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            return redirect('login')

    else:

        form = RegisterForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form
        }
    )


def login_view(request):

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:

                login(request, user)

                return redirect('idea_form')

            else:

                return render(
                    request,
                    'accounts/login.html',
                    {
                        'form': form,
                        'error': 'Invalid username or password'
                    }
                )

    else:

        form = LoginForm()

    return render(
        request,
        'accounts/login.html',
        {
            'form': form
        }
    )


def logout_view(request):
    return redirect('home')