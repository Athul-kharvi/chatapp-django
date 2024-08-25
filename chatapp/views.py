# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from .models import Room, Message, OTP, Profile
from .forms import SignUpForm, SignInForm
from .utils import generate_otp
from django.core.mail import send_mail
from django.contrib.auth.models import User



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
    if request.method != 'POST':
        return render(request, 'verify_otp.html')
    otp_code = request.POST['otp']
    user = request.user
    otp_instance = OTP.objects.get(user=user)

    if otp_instance.otp_code != otp_code:
        return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
    user.is_active = True
    user.save()
    login(request, user)
    return redirect('index') 

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if not form.is_valid():
            return render(request, 'signup.html', {'form': form})
        user = form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            generate_otp(user)  # Send OTP
            return redirect(reverse('verify_otp'))  # Redirect to OTP verification
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
    # Get or create the room (ensure the room name matches what you want)
    room, created = Room.objects.get_or_create(name=room_name)

    # Get the latest 50 messages in the room, ordered by timestamp
    messages = Message.objects.filter(room=room).order_by('-timestamp')[:50]
    messages = messages[::-1]  # Reverse the messages to have the oldest ones first

    # Retrieve the user and their profile
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    context = {
        "messages": messages,
        "user": user,
        "room_name": room_name,
        "profile": profile,  # Pass the profile to the template
    }

    return render(request, '_message.html', context)



def forgotPassword(request):

    return


def logout_view(request):
    logout(request)
    return redirect('signin')
