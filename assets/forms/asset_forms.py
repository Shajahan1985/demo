"""
Django forms for asset management.
"""
from django import forms
from django.db import models
from assets.models import Asset, OperatingSystem, Team, IPAddress


class AssetForm(forms.ModelForm):
    """Form for creating and updating assets."""
    
    class Meta:
        model = Asset
        fields = [
            'asset_tag',
            'system_type',
            'operating_system',
            'ip_address',
            'particulars',
            'assigned_to',
            'team',
            'warranty_expiration'
        ]
        widgets = {
            'asset_tag': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BIDC001'
            }),
            'system_type': forms.Select(attrs={'class': 'form-control'}),
            'operating_system': forms.Select(attrs={'class': 'form-control'}),
            'ip_address': forms.Select(attrs={'class': 'form-control'}),
            'particulars': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter detailed information about the asset'
            }),
            'assigned_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter person name'
            }),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'warranty_expiration': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'asset_tag': 'Asset Tag',
            'system_type': 'System Type',
            'operating_system': 'Operating System',
            'ip_address': 'IP Address',
            'particulars': 'Particulars',
            'assigned_to': 'Assigned To',
            'team': 'Team',
            'warranty_expiration': 'Warranty Expiration'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate operating system dropdown
        self.fields['operating_system'].queryset = OperatingSystem.objects.all()
        self.fields['operating_system'].empty_label = "Select Operating System"
        
        # Populate team dropdown
        self.fields['team'].queryset = Team.objects.all()
        self.fields['team'].empty_label = "Select Team"
        self.fields['team'].required = False
        
        # Populate IP address dropdown with only available IPs
        # For updates, include the currently assigned IP
        if self.instance and self.instance.pk and self.instance.ip_address:
            # Include current IP and all unassigned IPs
            available_ips = IPAddress.objects.filter(
                models.Q(is_assigned=False) | models.Q(pk=self.instance.ip_address.pk)
            )
        else:
            # Only show unassigned IPs for new assets
            available_ips = IPAddress.objects.filter(is_assigned=False)
        
        self.fields['ip_address'].queryset = available_ips
        self.fields['ip_address'].empty_label = "Select IP Address"
        self.fields['ip_address'].required = False
        
        # Set required fields
        self.fields['asset_tag'].required = True
        self.fields['system_type'].required = True
        self.fields['operating_system'].required = True
        self.fields['assigned_to'].required = False
        self.fields['particulars'].required = False
        self.fields['warranty_expiration'].required = False
    
    def clean_asset_tag(self):
        """Validate asset tag uniqueness."""
        asset_tag = self.cleaned_data.get('asset_tag')
        
        # Check if asset tag already exists (excluding current instance for updates)
        existing = Asset.objects.filter(asset_tag=asset_tag)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError("Asset tag already exists. Please use a unique asset tag.")
        
        return asset_tag


class FreeAssetForm(forms.Form):
    """Form for freeing assets with password confirmation."""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm'
        }),
        label='Password',
        required=True,
        help_text='Enter your admin password to confirm freeing this asset'
    )
    
    def clean_password(self):
        """Validate that password is provided."""
        password = self.cleaned_data.get('password')
        
        if not password:
            raise forms.ValidationError("Password is required to free an asset.")
        
        return password


class AttachmentForm(forms.Form):
    """Form for uploading attachments with size and type validation."""
    
    file = forms.FileField(
        label='File',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.gif,.bmp,.doc,.docx,.xls,.xlsx,.txt,.zip'
        }),
        help_text='Maximum file size: 10MB. Allowed types: PDF, images (JPG, PNG, GIF, BMP), documents (DOC, DOCX, XLS, XLSX, TXT, ZIP)'
    )
    
    # File validation constants (matching AttachmentService)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS = {
        'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip'
    }
    
    def clean_file(self):
        """Validate file size and type."""
        import os
        
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError("No file was uploaded.")
        
        # Validate file size
        if file.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError(
                f'File size exceeds the maximum limit of {self.MAX_FILE_SIZE / (1024 * 1024):.0f}MB'
            )
        
        # Validate file type
        file_extension = os.path.splitext(file.name)[1][1:].lower()  # Get extension without dot
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f'File type .{file_extension} is not allowed. Allowed types: {", ".join(sorted(self.ALLOWED_EXTENSIONS))}'
            )
        
        return file
