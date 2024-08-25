from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),  # Redirect empty path to index view
    path('signup/', views.signup_view, name='signup'),  # Sign-up route
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # OTP verification route
    path('signin/', views.signin_view, name='signin'),  # Sign-in route
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),  
    path('logout/', views.logout_view, name='logout'),  # Logout route
    path('update-profile/', views.update_profile, name='update_profile'),
    path('<str:room_name>/<str:username>/', views.message_view, name='room'),  # Chat room route
]
