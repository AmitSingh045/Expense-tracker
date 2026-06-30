from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer

# ----------------- HTML VIEWS -----------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        remember = request.POST.get('remember_me')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if remember:
                request.session.set_expiry(1209600) # 2 weeks
            else:
                request.session.set_expiry(0) # sessions expires when browser closes
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        p2 = request.POST.get('password_confirm')
        if p != p2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html')
        if User.objects.filter(username=u).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/register.html')
        if User.objects.filter(email=e).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=u, email=e, password=p)
        # Mock Email Verification
        user.is_email_verified = True # Auto-verify in dev, but token is created
        user.save()

        login(request, user)
        messages.success(request, "Account created successfully! Welcome aboard.")
        return redirect('dashboard')
    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            profile.phone_number = request.POST.get('phone_number', '')
            profile.preferred_currency = request.POST.get('preferred_currency', 'USD')
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            user.save()
            profile.save()
            messages.success(request, "Profile updated successfully.")
        elif action == 'change_password':
            old_p = request.POST.get('old_password')
            new_p = request.POST.get('new_password')
            new_p2 = request.POST.get('new_password_confirm')
            if not user.check_password(old_p):
                messages.error(request, "Current password is incorrect.")
            elif new_p != new_p2:
                messages.error(request, "New passwords do not match.")
            else:
                user.set_password(new_p)
                user.save()
                login(request, user) # keep logged in
                messages.success(request, "Password changed successfully.")
        elif action == 'delete_account':
            user.delete()
            messages.success(request, "Your account has been deleted permanently.")
            return redirect('login')
        elif action == 'toggle_theme':
            profile.dark_mode = request.POST.get('dark_mode') == 'true'
            profile.save()
            return JsonResponse({'status': 'success', 'dark_mode': profile.dark_mode})
        return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'currencies': Profile.CURRENCY_CHOICES
    })

def verify_email_view(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.save()
        messages.success(request, "Your email has been verified successfully! You can now log in.")
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired verification token.")
    return redirect('login')

# Simple placeholder views for forgot/reset password
def forgot_password_view(request):
    if request.method == 'POST':
        messages.success(request, "If your email is registered, we have sent a password reset link.")
        return redirect('login')
    return render(request, 'accounts/forgot_password.html')

def reset_password_view(request, token):
    if request.method == 'POST':
        messages.success(request, "Password reset successfully. You can now login.")
        return redirect('login')
    return render(request, 'accounts/reset_password.html')


# ----------------- REST API VIEWS -----------------

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
