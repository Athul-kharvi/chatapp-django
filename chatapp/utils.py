# utils.py
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def generate_otp(user):
    otp_code = ''.join(random.choices(string.digits, k=6))
    OTP.objects.create(user=user, otp=otp_code)
    send_otp_email(user.email, otp_code)

def send_otp_email(email, otp_code):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp_code}. It is valid for 10 minutes.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
