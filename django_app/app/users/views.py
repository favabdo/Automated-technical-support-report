from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile


# ---------------- ROLES ----------------
def get_role(user):
    try:
        return user.profile.role
    except:
        return None

def is_high_level(user):
    return get_role(user) in ['developer', 'owner']

def is_manager_level(user):
    return get_role(user) in ['developer', 'owner', 'admin']

def can_change_role(changer, target_role):
    changer_role = get_role(changer)
    # Developer لا يغير Owner والعكس
    protected = {'developer': ['owner'], 'owner': ['developer']}
    if changer_role in protected and target_role in protected[changer_role]:
        return False
    return True


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # دخول كزائر
        if action == 'visitor':
            visitor_user, created = User.objects.get_or_create(username='visitor')
            if created:
                visitor_user.set_password('visitor123')
                visitor_user.save()
                UserProfile.objects.create(
                    user=visitor_user,
                    phone_number='0000000000',
                    role='visitor',
                    is_first_login=False
                )
            login(request, visitor_user)
            return redirect('home')

        # دخول عادي برقم التلفون
        phone    = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            profile = UserProfile.objects.get(phone_number=phone)
            user = authenticate(request, username=profile.user.username, password=password)
            if user:
                login(request, user)
                if profile.is_first_login:
                    return redirect('change_password')
                return redirect('home')
            else:
                messages.error(request, 'رقم الهاتف أو كلمة المرور غير صحيحة')
        except UserProfile.DoesNotExist:
            messages.error(request, 'رقم الهاتف غير مسجل')

    return render(request, 'users/login.html')


# ---------------- CHANGE PASSWORD (أول دخول) ----------------
@login_required
def change_password(request):
    if request.method == 'POST':
        new_password  = request.POST.get('new_password')
        confirm       = request.POST.get('confirm_password')

        if new_password != confirm:
            messages.error(request, 'كلمات المرور غير متطابقة')
        elif len(new_password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        else:
            request.user.set_password(new_password)
            request.user.save()
            request.user.profile.is_first_login = False
            request.user.profile.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('home')

    return render(request, 'users/change_password.html')


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    return render(request, 'users/profile.html', {
        'role': get_role(request.user),
        'is_manager': is_manager_level(request.user),
    })


# ---------------- MANAGE USERS (developer/owner فقط) ----------------
@login_required
def manage_users(request):
    if not is_high_level(request.user):
        return redirect('home')

    profiles = UserProfile.objects.select_related('user').exclude(role='visitor')

    if request.method == 'POST':
        # إضافة مستخدم جديد
        phone    = request.POST.get('phone')
        name     = request.POST.get('name')
        role     = request.POST.get('role')

        if UserProfile.objects.filter(phone_number=phone).exists():
            messages.error(request, 'رقم الهاتف مسجل بالفعل')
        else:
            # الباسورد = آخر 5 أرقام من التلفون
            password = phone[-5:]
            username = phone
            user = User.objects.create_user(username=username, password=password)
            user.get_full_name = lambda: name
            user.first_name = name
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=phone,
                role=role,
                is_first_login=True
            )
            messages.success(request, f'تم إضافة {name} — الباسورد: {password}')

    return render(request, 'users/manage.html', {
        'profiles': profiles,
        'is_manager': True,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


# ---------------- CHANGE ROLE ----------------
@login_required
def change_role(request, user_id):
    if not is_high_level(request.user):
        return redirect('home')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            if can_change_role(request.user, profile.role):
                profile.role = new_role
                profile.save()
                messages.success(request, 'تم تغيير الصلاحية')
            else:
                messages.error(request, 'غير مسموح بتغيير صلاحية هذا المستخدم')
        except UserProfile.DoesNotExist:
            messages.error(request, 'المستخدم غير موجود')

    return redirect('manage_users')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')