from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import UserCreateForm, UserUpdateForm, RoleCreateForm, RoleUpdateForm, PasswordResetRequestForm, PasswordResetConfirmForm
import logging

logger = logging.getLogger(__name__)


class LoginView(View):
    """Handle user login requests"""
    
    def get(self, request):
        """Display login form"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})
    
    def post(self, request):
        """Process login credentials and create session"""
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                logger.info(f'Successful login for user: {username}')
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                logger.warning(f'Failed login attempt for username: {username}')
                messages.error(request, 'Invalid username or password.')
        else:
            # Log failed login attempt
            username = request.POST.get('username', 'unknown')
            logger.warning(f'Failed login attempt with invalid form data for username: {username}')
            messages.error(request, 'Invalid username or password.')
        
        return render(request, 'authentication/login.html', {'form': form})


class LogoutView(View):
    """Handle user logout requests"""
    
    def post(self, request):
        """Terminate session and clear authentication data"""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')
    
    def get(self, request):
        """Allow GET requests for logout as well"""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')


@login_required
def dashboard_view(request):
    """Simple dashboard view for authenticated users"""
    return render(request, 'authentication/dashboard.html')



class LoggingPermissionRequiredMixin(PermissionRequiredMixin):
    """Custom mixin that logs permission denials"""
    
    def handle_no_permission(self):
        """Log permission denial and call parent handler"""
        user = self.request.user
        required_perms = self.get_permission_required()
        logger.warning(
            f'Permission denied for user {user.username if user.is_authenticated else "anonymous"}: '
            f'Required permissions: {required_perms}'
        )
        return super().handle_no_permission()


class UserListView(LoginRequiredMixin, LoggingPermissionRequiredMixin, ListView):
    """Display list of all users (admin only)"""
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    
    def get_queryset(self):
        """Return all users with their groups prefetched"""
        return User.objects.all().prefetch_related('groups').order_by('username')


class UserCreateView(LoginRequiredMixin, LoggingPermissionRequiredMixin, CreateView):
    """Create new user with role assignment (admin only)"""
    model = User
    form_class = UserCreateForm
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.add_user'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'User "{self.object.username}" created successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, LoggingPermissionRequiredMixin, UpdateView):
    """Update existing user (admin only)"""
    model = User
    form_class = UserUpdateForm
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.change_user'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'User "{self.object.username}" updated successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_deactivate(request, pk):
    """Deactivate a user account"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    messages.success(request, f'User "{user.username}" has been deactivated.')
    return redirect('user_list')


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_reactivate(request, pk):
    """Reactivate a user account"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f'User "{user.username}" has been reactivated.')
    return redirect('user_list')


@login_required
@permission_required('auth.change_user', raise_exception=True)
def assign_permission_to_user(request, user_pk, permission_pk):
    """Assign an individual permission to a user"""
    from django.contrib.auth.models import Permission
    
    user = get_object_or_404(User, pk=user_pk)
    permission = get_object_or_404(Permission, pk=permission_pk)
    
    # Add permission to user's individual permissions
    user.user_permissions.add(permission)
    
    messages.success(
        request, 
        f'Permission "{permission.name}" has been assigned to user "{user.username}".'
    )
    return redirect('user_update', pk=user_pk)


@login_required
@permission_required('auth.change_user', raise_exception=True)
def revoke_permission_from_user(request, user_pk, permission_pk):
    """Revoke an individual permission from a user"""
    from django.contrib.auth.models import Permission
    
    user = get_object_or_404(User, pk=user_pk)
    permission = get_object_or_404(Permission, pk=permission_pk)
    
    # Remove permission from user's individual permissions
    user.user_permissions.remove(permission)
    
    messages.success(
        request, 
        f'Permission "{permission.name}" has been revoked from user "{user.username}".'
    )
    return redirect('user_update', pk=user_pk)



class RoleListView(LoginRequiredMixin, LoggingPermissionRequiredMixin, ListView):
    """Display list of all roles (admin only)"""
    model = Group
    template_name = 'authentication/role_list.html'
    context_object_name = 'roles'
    permission_required = 'auth.view_group'
    
    def get_queryset(self):
        """Return all roles with their permissions prefetched"""
        return Group.objects.all().prefetch_related('permissions').order_by('name')


class RoleCreateView(LoginRequiredMixin, LoggingPermissionRequiredMixin, CreateView):
    """Create new role with permission assignment (admin only)"""
    model = Group
    form_class = RoleCreateForm
    template_name = 'authentication/role_form.html'
    success_url = reverse_lazy('role_list')
    permission_required = 'auth.add_group'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'Role "{self.object.name}" created successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class RoleUpdateView(LoginRequiredMixin, LoggingPermissionRequiredMixin, UpdateView):
    """Update existing role (admin only)"""
    model = Group
    form_class = RoleUpdateForm
    template_name = 'authentication/role_form.html'
    success_url = reverse_lazy('role_list')
    permission_required = 'auth.change_group'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'Role "{self.object.name}" updated successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)



class PasswordResetRequestView(View):
    """Handle password reset request"""
    
    def get(self, request):
        """Display password reset request form"""
        form = PasswordResetRequestForm()
        return render(request, 'authentication/password_reset_request.html', {'form': form})
    
    def post(self, request):
        """Process password reset request and send email"""
        form = PasswordResetRequestForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Try to find user with this email (case-insensitive)
            try:
                user = User.objects.get(email__iexact=email)
                
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset link
                reset_link = request.build_absolute_uri(
                    f'/password-reset/confirm/{uid}/{token}/'
                )
                
                # Send email with reset link
                subject = 'Password Reset Request'
                message = f'''
You have requested to reset your password.

Please click the link below to reset your password:
{reset_link}

This link will expire in {settings.PASSWORD_RESET_TIMEOUT // 3600} hour(s).

If you did not request this password reset, please ignore this email.
'''
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(
                    request,
                    'Password reset link has been sent to your email address.'
                )
            except User.DoesNotExist:
                # Don't reveal whether email exists for security
                # Still show success message
                messages.success(
                    request,
                    'If an account exists with that email, a password reset link has been sent.'
                )
            
            return redirect('login')
        
        return render(request, 'authentication/password_reset_request.html', {'form': form})


class PasswordResetConfirmView(View):
    """Handle password reset confirmation"""
    
    def get(self, request, uidb64, token):
        """Display password reset form if token is valid"""
        try:
            # Decode user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Check if token is valid
            if default_token_generator.check_token(user, token):
                form = PasswordResetConfirmForm(user=user)
                return render(
                    request,
                    'authentication/password_reset_confirm.html',
                    {'form': form, 'validlink': True, 'uidb64': uidb64, 'token': token}
                )
            else:
                # Token is invalid or expired
                messages.error(request, 'This password reset link is invalid or has expired.')
                return render(
                    request,
                    'authentication/password_reset_confirm.html',
                    {'validlink': False}
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'This password reset link is invalid.')
            return render(
                request,
                'authentication/password_reset_confirm.html',
                {'validlink': False}
            )
    
    def post(self, request, uidb64, token):
        """Process password reset with new password"""
        try:
            # Decode user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Check if token is valid
            if not default_token_generator.check_token(user, token):
                messages.error(request, 'This password reset link is invalid or has expired.')
                return render(
                    request,
                    'authentication/password_reset_confirm.html',
                    {'validlink': False}
                )
            
            # Process form
            form = PasswordResetConfirmForm(user=user, data=request.POST)
            
            if form.is_valid():
                # Save new password
                form.save()
                
                # Invalidate all existing sessions for this user
                # Get all sessions and delete those belonging to this user
                for session in Session.objects.filter(expire_date__gte=timezone.now()):
                    session_data = session.get_decoded()
                    if session_data.get('_auth_user_id') == str(user.pk):
                        session.delete()
                
                messages.success(
                    request,
                    'Your password has been reset successfully. Please log in with your new password.'
                )
                return redirect('login')
            else:
                return render(
                    request,
                    'authentication/password_reset_confirm.html',
                    {'form': form, 'validlink': True, 'uidb64': uidb64, 'token': token}
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'This password reset link is invalid.')
            return render(
                request,
                'authentication/password_reset_confirm.html',
                {'validlink': False}
            )
