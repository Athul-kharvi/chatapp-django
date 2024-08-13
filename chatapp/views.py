# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from .models import Room, Message, OTP
from .forms import SignUpForm, SignInForm
from .utils import generate_otp
from django.core.mail import send_mail


def generate_otp(user):
    otp_instance = OTP.objects.create(user=user)
    otp_instance.generate_otp()
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp_instance.otp_code}. Please enter this code to complete your registration.',
        'ananthkharvi132@gmail.com',  # Replace with your email
        [user.email],
        fail_silently=False,
    )

def verify_otp(request):
    if request.method == 'POST':
        otp_code = request.POST['otp']
        user = request.user
        otp_instance = OTP.objects.get(user=user)
        
        if otp_instance.otp_code == otp_code:
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('index')  # Replace 'home' with your homepage URL
        else:
            # Handle invalid OTP
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'verify_otp.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                generate_otp(user)  # Send OTP
                return redirect(reverse('verify_otp'))  # Redirect to OTP verification
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})







def index_view(request):
    if request.user.is_authenticated:
        # Redirect authenticated users to the default room 'public-chat'
        return redirect(reverse('room', kwargs={'room_name': 'public-chat', 'username': request.user.username}))
    else:
        # Redirect unauthenticated users to the sign-in page
        return redirect('signin')

def signin_view(request):
    if request.method == 'POST':
        form = SignInForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(f"User {user.username} authenticated successfully.")  # Debugging print
            login(request, user)
            return redirect(reverse('room', kwargs={'room_name': 'public-chat', 'username': user.username}))
        else:
            print("Form is invalid")  # Debugging print
            print(form.errors)  # Debugging print
        return render(request, 'signin.html', {'form': form})
    else:
        form = SignInForm()
    return render(request, 'signin.html', {'form': form})


@login_required
def message_view(request, room_name, username):
    room, created = Room.objects.get_or_create(room_name='public-chat')
    messages = Message.objects.filter(room=room)
    print(type(username))
    context = {
        "messages": messages,
        "user": username,
        "room_name": room_name,
    }
    
    return render(request, '_message.html', context)


def logout_view(request):
    logout(request)
    return redirect('signin')
