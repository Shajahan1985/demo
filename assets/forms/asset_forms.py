"""
Django forms for asset management.
"""
from django import forms
from django.db import models
from assets.models import Asset, OperatingSystem, Team, IPAddress, NetworkDevice


class HierarchicalTeamChoiceField(forms.ModelChoiceField):
    """Custom form field for displaying teams hierarchically."""
    
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = Team.objects.get_hierarchy()
        super().__init__(*args, **kwargs)
    
    def label_from_instance(self, obj):
        """Return label with hierarchy indentation."""
        if obj.parent:
            return f"  └─ {obj.name}"
        return obj.name


class AssetForm(forms.ModelForm):
    """Form for creating and updating assets."""
    
    parent_team = forms.ModelChoiceField(
        queryset=Team.objects.get_parent_teams(),
        required=False,
        empty_label="Select Team",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_parent_team',
            'onchange': 'handleParentTeamChange(this.value)'
        }),
        label='Team'
    )
    
    sub_team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        empty_label="Select Sub-Team",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_sub_team',
            'style': 'display:none;'
        }),
        label='Sub-Team'
    )
    
    team = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Asset
        fields = [
            'asset_tag',
            'system_type',
            'hardware_serial_number',
            'manufacturer',
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
            'system_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hardware_serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_hardware_serial_number',
                'placeholder': 'Enter hardware serial number'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dell, HP, Lenovo'
            }),
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
            'warranty_expiration': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'asset_tag': 'Asset Tag',
            'system_type': 'System Type',
            'hardware_serial_number': 'Hardware Serial Number',
            'manufacturer': 'Manufacturer',
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
        
        # Hardware serial number is not required by default (will be validated in clean())
        self.fields['hardware_serial_number'].required = False
        
        # Handle team cascading dropdown - for editing existing assets
        if self.instance and self.instance.pk and self.instance.team:
            current_team = self.instance.team
            if current_team.parent:
                # Asset is assigned to a sub-team
                self.fields['parent_team'].initial = current_team.parent
                self.fields['sub_team'].queryset = current_team.parent.sub_teams.all()
                self.fields['sub_team'].initial = current_team
                self.fields['sub_team'].widget.attrs['style'] = ''
            else:
                # Asset is assigned to a parent team
                self.fields['parent_team'].initial = current_team
            self.fields['team'].initial = current_team
        
        # Handle team cascading dropdown - for form submission with POST data
        if self.data:
            try:
                parent_team_id = self.data.get('parent_team')
                if parent_team_id:
                    parent_team = Team.objects.get(pk=parent_team_id)
                    self.fields['sub_team'].queryset = parent_team.sub_teams.all()
            except (ValueError, Team.DoesNotExist):
                pass
        
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
        self.fields['operating_system'].required = False  # Made optional to allow manual entry
        self.fields['assigned_to'].required = False
        self.fields['particulars'].required = False
        self.fields['warranty_expiration'].required = False
        self.fields['parent_team'].required = False
        self.fields['sub_team'].required = False
    
    def clean(self):
        """Custom validation to set the team field based on parent_team and sub_team."""
        cleaned_data = super().clean()
        parent_team = cleaned_data.get('parent_team')
        sub_team = cleaned_data.get('sub_team')
        system_type = cleaned_data.get('system_type')
        hardware_serial_number = cleaned_data.get('hardware_serial_number')
        
        # Validate hardware serial number for Laptop and All-in-One PC
        if system_type in ['Laptop', 'All-in-One PC']:
            if not hardware_serial_number or not hardware_serial_number.strip():
                self.add_error('hardware_serial_number', 'Hardware serial number is required for Laptop and All-in-One PC.')
        
        # Determine which team to assign
        if sub_team:
            cleaned_data['team'] = sub_team
        elif parent_team:
            cleaned_data['team'] = parent_team
        else:
            cleaned_data['team'] = None
        
        return cleaned_data
    
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


class ReassignmentForm(forms.Form):
    """Form for reassigning freed systems back to active status."""
    
    assigned_to = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter person name'
        }),
        label='Assigned To'
    )
    
    parent_team = forms.ModelChoiceField(
        queryset=Team.objects.get_parent_teams(),
        required=False,
        empty_label="Select Team",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_parent_team'
        }),
        label='Team'
    )
    
    sub_team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        empty_label="Select Sub-Team",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_sub_team',
            'style': 'display:none;'
        }),
        label='Sub-Team'
    )
    
    team = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        required=True,
        widget=forms.HiddenInput()
    )
    
    manual_ip = forms.GenericIPAddressField(
        protocol='IPv4',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_manual_ip',
            'placeholder': 'e.g., 192.168.1.100'
        }),
        label='IP Address'
    )
    
    operating_system = forms.ModelChoiceField(
        queryset=OperatingSystem.objects.all(),
        required=False,
        empty_label="Select Operating System",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_operating_system'
        }),
        label='Operating System'
    )
    
    os_manual_entry = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_os_manual_entry',
            'placeholder': 'Or enter OS manually'
        }),
        label='Manual OS Entry'
    )
    
    system_type = forms.ChoiceField(
        choices=Asset.SYSTEM_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_system_type'
        }),
        label='System Type'
    )
    
    manufacturer = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Dell, HP, Lenovo'
        }),
        label='Manufacturer'
    )
    
    particulars = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter detailed information about the asset'
        }),
        label='Particulars'
    )
    
    warranty_expiration = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Warranty Expiration'
    )
    
    def __init__(self, *args, **kwargs):
        asset = kwargs.pop('asset', None)
        super().__init__(*args, **kwargs)
        
        # Handle team cascading dropdown - for form submission with POST data
        if self.data:
            try:
                parent_team_id = self.data.get('parent_team')
                if parent_team_id:
                    parent_team = Team.objects.get(pk=parent_team_id)
                    self.fields['sub_team'].queryset = parent_team.sub_teams.all()
            except (ValueError, Team.DoesNotExist):
                pass
        
        # Pre-populate fields with current asset values if asset provided
        if asset:
            self.fields['assigned_to'].initial = asset.assigned_to or ''
            self.fields['system_type'].initial = asset.system_type
            self.fields['manufacturer'].initial = asset.manufacturer or ''
            self.fields['particulars'].initial = asset.particulars or ''
            self.fields['warranty_expiration'].initial = asset.warranty_expiration
            
            if asset.operating_system:
                self.fields['operating_system'].initial = asset.operating_system
            
            if asset.team:
                if asset.team.parent:
                    self.fields['parent_team'].initial = asset.team.parent
                    self.fields['sub_team'].queryset = asset.team.parent.sub_teams.all()
                    self.fields['sub_team'].initial = asset.team
                    self.fields['sub_team'].widget.attrs['style'] = ''
                else:
                    self.fields['parent_team'].initial = asset.team
                self.fields['team'].initial = asset.team
            
            if asset.ip_address:
                # Include current IP in queryset
                self.fields['ip_address'].queryset = IPAddress.objects.filter(
                    models.Q(is_assigned=False) | models.Q(pk=asset.ip_address.pk)
                )
                self.fields['ip_address'].initial = asset.ip_address
            elif asset.manual_ip:
                self.fields['manual_ip'].initial = asset.manual_ip
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        parent_team = cleaned_data.get('parent_team')
        sub_team = cleaned_data.get('sub_team')
        manual_ip = cleaned_data.get('manual_ip')
        
        # Manual IP is now required (handled by field definition)
        # No need for additional IP validation since we only have one IP field
        
        # Determine which team to assign
        if sub_team:
            cleaned_data['team'] = sub_team
        elif parent_team:
            cleaned_data['team'] = parent_team
        else:
            raise forms.ValidationError("Please select a team.")
        
        return cleaned_data
    
    def clean_manual_ip(self):
        """Validate manual IP format."""
        manual_ip = self.cleaned_data.get('manual_ip')
        
        if manual_ip:
            # GenericIPAddressField already validates IPv4 format
            # Additional validation can be added here if needed
            pass
        
        return manual_ip


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



class NetworkDeviceForm(forms.ModelForm):
    """Form for creating and updating network devices."""
    
    class Meta:
        model = NetworkDevice
        fields = ['device_type', 'device_name', 'ip_address']
        widgets = {
            'device_type': forms.Select(attrs={'class': 'form-control'}),
            'device_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter device name or description'
            }),
            'ip_address': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show only unassigned IPs for new devices
        if self.instance and self.instance.pk:
            # For updates, include current IP and unassigned IPs
            self.fields['ip_address'].queryset = IPAddress.objects.filter(
                models.Q(is_assigned=False) | models.Q(pk=self.instance.ip_address.pk)
            )
        else:
            # For new devices, only show unassigned IPs
            self.fields['ip_address'].queryset = IPAddress.objects.filter(is_assigned=False)
        
        self.fields['ip_address'].empty_label = "Select IP Address"
