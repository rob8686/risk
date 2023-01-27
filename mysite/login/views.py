from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import LoginForm


def createAccount(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login:login')

    context = {'form': form}
    return render(request, 'login/create_account.html', context)


def loginUser(request):
    context = {}
    form = LoginForm(request.POST)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username,password=password)

        if user is not None:
            login(request, user)
            return redirect('risk:index')
        else:
            messages.info(request, 'Username OR password is incorrect')

    context['form'] = form

    return render(request, 'login/login_page.html', context)

def logoutUser(request):
    logout(request)
    return redirect('risk:index')

