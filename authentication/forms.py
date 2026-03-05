from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
import logging

logger = logging.getLogger(__name__)


class UserCreateForm(UserCreationForm):
    """Form for creating new users with role assignment"""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        help_text='Select a role to assign to this user.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
    
    def clean_username(self):
        """Validate and sanitize username"""
        username = self.cleaned_data.get('username')
        
        # Check for empty or whitespace-only username
        if not username or not username.strip():
            logger.warning(f"Attempted user creation with empty/whitespace username")
            raise ValidationError('Username cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        username = username.strip()
        
        # Check for SQL injection patterns (basic protection)
        sql_patterns = [
            r"(\bOR\b|\bAND\b).*=",  # OR/AND with equals
            r"[';\"--]",  # SQL special characters
            r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b)",  # SQL keywords
        ]
        for pattern in sql_patterns:
            if re.search(pattern, username, re.IGNORECASE):
                logger.warning(f"Attempted user creation with suspicious username: {username}")
                raise ValidationError('Username contains invalid characters.')
        
        return username
    
    def clean_email(self):
        """Validate and sanitize email format"""
        email = self.cleaned_data.get('email')
        
        # Check for empty or whitespace-only email
        if not email or not email.strip():
            logger.warning(f"Attempted user creation with empty/whitespace email")
            raise ValidationError('Email cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        email = email.strip()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            logger.warning(f"Attempted user creation with invalid email format: {email}")
            raise ValidationError('Enter a valid email address.')
        
        # Check for XSS patterns in email
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
        ]
        for pattern in xss_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                logger.warning(f"Attempted user creation with suspicious email: {email}")
                raise ValidationError('Email contains invalid characters.')
        
        return email
    
    def save(self, commit=True):
        """Save user and assign role if provided"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Assign role if provided
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
        
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users"""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        help_text='Select a role to assign to this user.'
    )
    is_active = forms.BooleanField(
        required=False,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )
    individual_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select individual permissions to assign directly to this user (in addition to role permissions).'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'role', 'individual_permissions')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial role if user has one
        if self.instance and self.instance.pk:
            user_groups = self.instance.groups.all()
            if user_groups.exists():
                self.fields['role'].initial = user_groups.first()
            self.fields['is_active'].initial = self.instance.is_active
            # Set initial individual permissions
            self.fields['individual_permissions'].initial = self.instance.user_permissions.all()
        
        # Filter permissions to show only relevant ones
        self.fields['individual_permissions'].queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    
    def clean_username(self):
        """Validate and sanitize username"""
        username = self.cleaned_data.get('username')
        
        # Check for empty or whitespace-only username
        if not username or not username.strip():
            logger.warning(f"Attempted user update with empty/whitespace username")
            raise ValidationError('Username cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        username = username.strip()
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bOR\b|\bAND\b).*=",
            r"[';\"--]",
            r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, username, re.IGNORECASE):
                logger.warning(f"Attempted user update with suspicious username: {username}")
                raise ValidationError('Username contains invalid characters.')
        
        return username
    
    def clean_email(self):
        """Validate and sanitize email format"""
        email = self.cleaned_data.get('email')
        
        # Check for empty or whitespace-only email
        if not email or not email.strip():
            logger.warning(f"Attempted user update with empty/whitespace email")
            raise ValidationError('Email cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        email = email.strip()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            logger.warning(f"Attempted user update with invalid email format: {email}")
            raise ValidationError('Enter a valid email address.')
        
        # Check for XSS patterns
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
        ]
        for pattern in xss_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                logger.warning(f"Attempted user update with suspicious email: {email}")
                raise ValidationError('Email contains invalid characters.')
        
        return email
    
    def clean_first_name(self):
        """Sanitize first name"""
        first_name = self.cleaned_data.get('first_name', '')
        if first_name:
            first_name = first_name.strip()
            # Check for XSS patterns
            xss_patterns = [r'<script', r'javascript:', r'onerror=', r'onclick=']
            for pattern in xss_patterns:
                if re.search(pattern, first_name, re.IGNORECASE):
                    logger.warning(f"Attempted user update with suspicious first_name: {first_name}")
                    raise ValidationError('First name contains invalid characters.')
        return first_name
    
    def clean_last_name(self):
        """Sanitize last name"""
        last_name = self.cleaned_data.get('last_name', '')
        if last_name:
            last_name = last_name.strip()
            # Check for XSS patterns
            xss_patterns = [r'<script', r'javascript:', r'onerror=', r'onclick=']
            for pattern in xss_patterns:
                if re.search(pattern, last_name, re.IGNORECASE):
                    logger.warning(f"Attempted user update with suspicious last_name: {last_name}")
                    raise ValidationError('Last name contains invalid characters.')
        return last_name
    
    def save(self, commit=True):
        """Save user and update role and individual permissions"""
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Update role - clear existing and add new if provided
            user.groups.clear()
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
            
            # Update individual permissions
            individual_permissions = self.cleaned_data.get('individual_permissions')
            if individual_permissions is not None:
                user.user_permissions.set(individual_permissions)
        
        return user



class RoleCreateForm(forms.ModelForm):
    """Form for creating new roles (groups) with permission selection"""
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select permissions to assign to this role.'
    )
    
    class Meta:
        model = Group
        fields = ('name', 'permissions')
    
    def clean_name(self):
        """Validate and sanitize role name"""
        name = self.cleaned_data.get('name')
        
        # Check for empty or whitespace-only name
        if not name or not name.strip():
            logger.warning(f"Attempted role creation with empty/whitespace name")
            raise ValidationError('Role name cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        name = name.strip()
        
        # Check for XSS patterns
        xss_patterns = [r'<script', r'javascript:', r'onerror=', r'onclick=']
        for pattern in xss_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                logger.warning(f"Attempted role creation with suspicious name: {name}")
                raise ValidationError('Role name contains invalid characters.')
        
        return name
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter permissions to show only relevant ones (exclude built-in content types)
        self.fields['permissions'].queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    
    def save(self, commit=True):
        """Save role and assign permissions"""
        role = super().save(commit=False)
        
        if commit:
            role.save()
            # Assign permissions
            permissions = self.cleaned_data.get('permissions')
            if permissions:
                role.permissions.set(permissions)
        
        return role


class RoleUpdateForm(forms.ModelForm):
    """Form for updating existing roles with permission selection"""
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select permissions to assign to this role.'
    )
    
    class Meta:
        model = Group
        fields = ('name', 'permissions')
    
    def clean_name(self):
        """Validate and sanitize role name"""
        name = self.cleaned_data.get('name')
        
        # Check for empty or whitespace-only name
        if not name or not name.strip():
            logger.warning(f"Attempted role update with empty/whitespace name")
            raise ValidationError('Role name cannot be empty or contain only whitespace.')
        
        # Sanitize: strip whitespace
        name = name.strip()
        
        # Check for XSS patterns
        xss_patterns = [r'<script', r'javascript:', r'onerror=', r'onclick=']
        for pattern in xss_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                logger.warning(f"Attempted role update with suspicious name: {name}")
                raise ValidationError('Role name contains invalid characters.')
        
        return name
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter permissions to show only relevant ones
        self.fields['permissions'].queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
        
        # Set initial permissions if role exists
        if self.instance and self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.all()
    
    def save(self, commit=True):
        """Save role and update permissions"""
        role = super().save(commit=False)
        
        if commit:
            role.save()
            # Update permissions
            permissions = self.cleaned_data.get('permissions')
            role.permissions.set(permissions)
        
        return role


class PasswordResetRequestForm(forms.Form):
    """Form for requesting a password reset"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text='Enter your registered email address.'
    )
    
    def clean_email(self):
        """Validate that the email exists in the system"""
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            # Don't reveal whether email exists for security
            # Just return the email, validation happens in view
            pass
        return email


class PasswordResetConfirmForm(forms.Form):
    """Form for confirming password reset with new password"""
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter your new password.'
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password again for verification.'
    )
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_new_password2(self):
        """Validate that passwords match"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        
        return password2
    
    def clean_new_password1(self):
        """Validate password strength"""
        from django.contrib.auth.password_validation import validate_password
        
        password = self.cleaned_data.get('new_password1')
        if password and self.user:
            validate_password(password, self.user)
        
        return password
    
    def save(self, commit=True):
        """Save the new password"""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
