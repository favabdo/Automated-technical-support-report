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
    protected = {'developer': ['owner'], 'owner': ['developer']}
    if changer_role in protected and target_role in protected[changer_role]:
        return False
    return True


# ---------------- LOGIN ----------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

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
                    agent_id='visitor',
                    role='visitor',
                    is_first_login=False
                )
            login(request, visitor_user)
            return redirect('home')

        # دخول بالـ agent_id والباسورد
        agent_id = request.POST.get('agent_id', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            profile = UserProfile.objects.get(agent_id=agent_id)
            user = authenticate(request, username=profile.user.username, password=password)
            if user:
                login(request, user)
                if profile.is_first_login:
                    return redirect('change_password')
                return redirect('home')
            else:
                messages.error(request, 'الـ ID أو كلمة المرور غير صحيحة')
        except UserProfile.DoesNotExist:
            messages.error(request, 'هذا الـ ID غير مسجل')

    return render(request, 'users/login.html')


# ---------------- CHANGE PASSWORD (أول دخول - إجباري) ----------------
@login_required
def change_password(request):
    if request.method == 'POST':
        new_password     = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        new_email        = request.POST.get('email', '').strip()  # اختياري

        if not new_password:
            messages.error(request, 'كلمة المرور مطلوبة')
        elif new_password == request.user.profile.agent_id:
            messages.error(request, 'كلمة المرور الجديدة لا يمكن أن تكون نفس الـ ID')
        elif len(new_password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        elif new_password != confirm_password:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
        else:
            request.user.set_password(new_password)
            if new_email:
                request.user.email = new_email
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
    if request.method == 'POST':
        action = request.POST.get('action')

        # تغيير الإيميل
        if action == 'change_email':
            new_email = request.POST.get('new_email', '').strip()
            if new_email:
                request.user.email = new_email
                request.user.save()
                messages.success(request, 'تم تحديث البريد الإلكتروني')
            else:
                messages.error(request, 'يرجى إدخال بريد إلكتروني صحيح')

        # تغيير الباسورد
        elif action == 'change_password':
            old_password     = request.POST.get('old_password', '')
            new_password     = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            if not request.user.check_password(old_password):
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
            elif new_password == request.user.profile.agent_id:
                messages.error(request, 'كلمة المرور لا يمكن أن تكون نفس الـ ID')
            elif len(new_password) < 6:
                messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            elif new_password != confirm_password:
                messages.error(request, 'كلمتا المرور غير متطابقتين')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'تم تغيير كلمة المرور بنجاح')

        return redirect('profile')

    return render(request, 'users/profile.html', {
        'role':       get_role(request.user),
        'is_manager': is_manager_level(request.user),
    })


# ---------------- MANAGE USERS ----------------
@login_required
def manage_users(request):
    if not is_high_level(request.user):
        return redirect('home')

    profiles = UserProfile.objects.select_related('user').exclude(role='visitor')

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '').strip()
        name     = request.POST.get('name', '').strip()
        role     = request.POST.get('role', 'agent')

        if not agent_id or not name:
            messages.error(request, 'الاسم والـ ID مطلوبان')
        elif UserProfile.objects.filter(agent_id=agent_id).exists():
            messages.error(request, 'هذا الـ ID مسجل بالفعل')
        else:
            # username = agent_id، باسورد افتراضي = agent_id
            user = User.objects.create_user(
                username=agent_id,
                password=agent_id,
                first_name=name
            )
            UserProfile.objects.create(
                user=user,
                agent_id=agent_id,
                role=role,
                is_first_login=True
            )
            messages.success(request, f'تم إضافة {name} — ID: {agent_id} — الباسورد الافتراضي: {agent_id}')

    return render(request, 'users/manage.html', {
        'profiles':     profiles,
        'is_manager':   True,
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
