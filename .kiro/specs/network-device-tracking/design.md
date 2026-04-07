# Design Document: Network Device Tracking

## Overview

The network device tracking feature extends the existing IP address management system to track non-system network devices (cameras, printers, punching machines, mobiles) that consume IP addresses but are not part of the asset tracking system. This feature provides visibility into network resource usage and prevents IP address conflicts by integrating with the existing IPAddress model.

The design follows Django's MVT (Model-View-Template) architecture and integrates seamlessly with the existing asset management system. Network devices are stored separately from assets but share the same IP address management infrastructure to ensure consistency and prevent conflicts.

Key design principles:
- Separation of concerns: Network devices are distinct from IT assets
- Reuse existing IP management: Leverage IPAddress model and IPManagementService
- Consistent user experience: Follow existing UI patterns and admin-only access controls
- Data integrity: Enforce IP address uniqueness across both assets and network devices

## Architecture

### System Components

The feature consists of four main layers:

1. **Data Layer**: NetworkDevice model integrated with existing IPAddress model
2. **Service Layer**: NetworkDeviceService for business logic and IP management integration
3. **View Layer**: Django class-based views for CRUD operations
4. **Template Layer**: HTML templates following existing design patterns

### Integration Points

- **IPAddress Model**: Network devices reference the same IPAddress model used by assets
- **IPManagementService**: Reuse existing service for IP assignment/release operations
- **AdminRequiredMixin**: Use existing permission mixin for access control
- **Free IPs Page**: Extend existing view to display network device information

### Data Flow

1. **Create Network Device**:
   - Admin submits form → View validates → Service checks IP availability → IPManagementService assigns IP → NetworkDevice created

2. **Update Network Device**:
   - Admin submits form → View validates → Service checks new IP availability → IPManagementService releases old IP and assigns new IP → NetworkDevice updated

3. **Delete Network Device**:
   - Admin confirms deletion → View processes → Service deletes device → IPManagementService releases IP

4. **Display on Free IPs Page**:
   - User requests page → View queries IPAddress with related NetworkDevice → Template renders with device information

## Components and Interfaces

### Models

#### NetworkDevice Model

```python
class NetworkDevice(models.Model):
    """Model for tracking non-system network devices."""
    
    DEVICE_TYPE_CHOICES = [
        ('Camera', 'Camera'),
        ('Printer', 'Printer'),
        ('Punching Machine', 'Punching Machine'),
        ('Mobile', 'Mobile'),
        ('Other', 'Other'),
    ]
    
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE_CHOICES)
    device_name = models.CharField(max_length=255)
    ip_address = models.OneToOneField(
        IPAddress, 
        on_delete=models.PROTECT, 
        related_name='network_device'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['device_name']
        indexes = [
            models.Index(fields=['device_type']),
            models.Index(fields=['device_name']),
        ]
    
    def __str__(self):
        return f"{self.device_name} ({self.device_type})"
```

**Design Decisions**:
- OneToOneField ensures each IP can only be assigned to one network device
- PROTECT on_delete prevents accidental IP deletion when device exists
- Indexes on device_type and device_name for efficient filtering and searching
- Separate from Asset model to avoid cluttering asset inventory

### Forms

#### NetworkDeviceForm

```python
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
```

### Services

#### NetworkDeviceService

```python
class NetworkDeviceService:
    """Service for network device business logic."""
    
    @staticmethod
    def create_network_device(data, user):
        """
        Create network device with IP assignment.
        
        Args:
            data: Dictionary with device_type, device_name, ip_address_id
            user: User creating the device
        
        Returns:
            NetworkDevice: Created device instance
        
        Raises:
            ValidationError: If IP is already assigned
        """
        with transaction.atomic():
            ip_address = IPAddress.objects.get(id=data['ip_address_id'])
            
            if ip_address.is_assigned:
                raise ValidationError({'ip_address': 'IP address already in use'})
            
            device = NetworkDevice.objects.create(
                device_type=data['device_type'],
                device_name=data['device_name'],
                ip_address=ip_address
            )
            
            # Mark IP as assigned using existing service
            IPManagementService.assign_ip_to_network_device(ip_address, device)
            
            return device
    
    @staticmethod
    def update_network_device(device, data, user):
        """
        Update network device with IP change handling.
        
        Args:
            device: NetworkDevice instance to update
            data: Dictionary with updated fields
            user: User updating the device
        
        Returns:
            NetworkDevice: Updated device instance
        
        Raises:
            ValidationError: If new IP is already assigned
        """
        with transaction.atomic():
            old_ip = device.ip_address
            new_ip_id = data.get('ip_address_id')
            
            if new_ip_id and str(old_ip.id) != str(new_ip_id):
                new_ip = IPAddress.objects.get(id=new_ip_id)
                
                if new_ip.is_assigned:
                    raise ValidationError({'ip_address': 'IP address already in use'})
                
                # Release old IP
                IPManagementService.release_ip(old_ip)
                
                # Assign new IP
                device.ip_address = new_ip
                IPManagementService.assign_ip_to_network_device(new_ip, device)
            
            # Update other fields
            device.device_type = data.get('device_type', device.device_type)
            device.device_name = data.get('device_name', device.device_name)
            device.save()
            
            return device
    
    @staticmethod
    def delete_network_device(device, user):
        """
        Delete network device and release IP.
        
        Args:
            device: NetworkDevice instance to delete
            user: User deleting the device
        """
        with transaction.atomic():
            ip_address = device.ip_address
            device.delete()
            IPManagementService.release_ip(ip_address)
```

### Views

#### NetworkDeviceListView

```python
class NetworkDeviceListView(AdminRequiredMixin, ListView):
    """Display all network devices."""
    model = NetworkDevice
    template_name = 'assets/network_device_list.html'
    context_object_name = 'devices'
    
    def get_queryset(self):
        return NetworkDevice.objects.select_related('ip_address').order_by('device_name')
```

#### NetworkDeviceCreateView

```python
class NetworkDeviceCreateView(AdminRequiredMixin, CreateView):
    """Create new network device."""
    model = NetworkDevice
    form_class = NetworkDeviceForm
    template_name = 'assets/network_device_form.html'
    success_url = reverse_lazy('network_device_list')
    
    def form_valid(self, form):
        try:
            data = {
                'device_type': form.cleaned_data['device_type'],
                'device_name': form.cleaned_data['device_name'],
                'ip_address_id': form.cleaned_data['ip_address'].id
            }
            device = NetworkDeviceService.create_network_device(data, self.request.user)
            messages.success(self.request, f'Network device {device.device_name} created successfully.')
            return redirect(self.success_url)
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
```

#### NetworkDeviceUpdateView

```python
class NetworkDeviceUpdateView(AdminRequiredMixin, UpdateView):
    """Update existing network device."""
    model = NetworkDevice
    form_class = NetworkDeviceForm
    template_name = 'assets/network_device_form.html'
    success_url = reverse_lazy('network_device_list')
    
    def form_valid(self, form):
        try:
            device = self.get_object()
            data = {
                'device_type': form.cleaned_data['device_type'],
                'device_name': form.cleaned_data['device_name'],
                'ip_address_id': form.cleaned_data['ip_address'].id
            }
            updated_device = NetworkDeviceService.update_network_device(device, data, self.request.user)
            messages.success(self.request, f'Network device {updated_device.device_name} updated successfully.')
            return redirect(self.success_url)
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
```

#### NetworkDeviceDeleteView

```python
class NetworkDeviceDeleteView(AdminRequiredMixin, View):
    """Delete network device with confirmation."""
    
    def get(self, request, pk):
        device = get_object_or_404(NetworkDevice, pk=pk)
        return render(request, 'assets/network_device_confirm_delete.html', {'device': device})
    
    def post(self, request, pk):
        device = get_object_or_404(NetworkDevice, pk=pk)
        device_name = device.device_name
        NetworkDeviceService.delete_network_device(device, request.user)
        messages.success(request, f'Network device {device_name} deleted successfully.')
        return redirect('network_device_list')
```

### IPManagementService Extensions

The existing IPManagementService needs to be extended to support network devices:

```python
# Add to IPManagementService class

@staticmethod
def assign_ip_to_network_device(ip_address, network_device):
    """
    Assign IP address to network device.
    
    Args:
        ip_address: IPAddress instance
        network_device: NetworkDevice instance
    """
    ip_address.is_assigned = True
    ip_address.assigned_to_asset = None  # Network devices don't use this field
    ip_address.save()

@staticmethod
def get_ip_occupant_info(ip_address):
    """
    Get information about what occupies an IP address.
    
    Args:
        ip_address: IPAddress instance
    
    Returns:
        dict: {'type': 'asset'|'network_device'|'free', 'name': str, 'object': Asset|NetworkDevice|None}
    """
    if hasattr(ip_address, 'network_device'):
        return {
            'type': 'network_device',
            'name': ip_address.network_device.device_name,
            'object': ip_address.network_device
        }
    elif ip_address.assigned_to_asset:
        return {
            'type': 'asset',
            'name': ip_address.assigned_to_asset.assigned_to or 'Unassigned',
            'object': ip_address.assigned_to_asset
        }
    else:
        return {
            'type': 'free',
            'name': None,
            'object': None
        }
```

### Free IPs Page Integration

The existing FreeIPsView needs to be updated to include network device information:

```python
# Update FreeIPsView.get_context_data()

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    # Get IP ranges with occupant information
    ip_ranges = IPManagementService.get_all_ips_by_range()
    
    # Enhance each IP with occupant info
    for range_pattern, ips in ip_ranges.items():
        for ip_data in ips:
            ip_address = ip_data['ip_object']
            occupant_info = IPManagementService.get_ip_occupant_info(ip_address)
            ip_data['occupant_type'] = occupant_info['type']
            ip_data['occupant_name'] = occupant_info['name']
    
    context['ip_ranges'] = ip_ranges
    
    # Add search functionality
    search_query = self.request.GET.get('search', '').strip()
    if search_query:
        context['search_query'] = search_query
        context['ip_ranges'] = self._filter_ips_by_search(ip_ranges, search_query)
    
    return context

def _filter_ips_by_search(self, ip_ranges, query):
    """Filter IP ranges by search query matching IP address or occupant name."""
    filtered_ranges = {}
    query_lower = query.lower()
    
    for range_pattern, ips in ip_ranges.items():
        filtered_ips = []
        for ip_data in ips:
            # Match against IP address
            if query_lower in ip_data['address'].lower():
                filtered_ips.append(ip_data)
                continue
            
            # Match against occupant name
            if ip_data.get('occupant_name') and query_lower in ip_data['occupant_name'].lower():
                filtered_ips.append(ip_data)
        
        if filtered_ips:
            filtered_ranges[range_pattern] = filtered_ips
    
    return filtered_ranges
```

## Data Models

### NetworkDevice Table Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| device_type | VARCHAR(50) | NOT NULL | Type from predefined choices |
| device_name | VARCHAR(255) | NOT NULL | Device name or description |
| ip_address_id | INTEGER | FOREIGN KEY, UNIQUE, NOT NULL | Reference to IPAddress |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

### Relationships

- NetworkDevice → IPAddress: One-to-One (each device has exactly one IP)
- IPAddress ← NetworkDevice: One-to-One (each IP can be assigned to at most one network device)
- IPAddress ← Asset: One-to-Many (existing relationship, unchanged)

### Database Indexes

- Primary key index on `id`
- Unique index on `ip_address_id` (enforced by OneToOneField)
- Index on `device_type` for filtering
- Index on `device_name` for searching


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:

- Properties 1.1, 1.2, 1.3, 1.4 (individual field storage) can be combined into a single comprehensive property about complete device data storage
- Properties 2.2 and 3.3 (IP marking as occupied) are the same operation in different contexts - can be combined
- Properties 3.2 and 4.2 (IP marking as free) are the same operation in different contexts - can be combined
- Properties 2.3 and 3.4 (IP conflict validation) are the same validation in different contexts - can be combined
- Properties 6.1, 6.2, 6.4, 6.5 (search functionality) can be combined into comprehensive search properties
- Properties 10.1, 10.2, 10.3 (IP validation) can be combined into a single validation property

### Property 1: Complete Device Data Storage

For any network device created in the system, the device record shall contain a valid device type from the predefined list, a non-empty device name, an associated IP address, and both creation and modification timestamps.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: IP Address Uniqueness Across Network Devices

For any two distinct network devices, they shall not share the same IP address.

**Validates: Requirements 1.5**

### Property 3: Network Device Creation

For any valid device data (device type, device name, and available IP address), creating a network device shall result in a new device record existing in the database with all required fields populated.

**Validates: Requirements 2.1, 2.4**

### Property 4: IP Assignment on Create and Update

For any network device operation (create or update) that assigns an IP address to a device, the IP address shall be marked as occupied (is_assigned=True) after the operation completes.

**Validates: Requirements 2.2, 3.3**

### Property 5: IP Conflict Prevention

For any IP address already assigned to a network device or asset, attempting to create or update a network device with that IP address shall raise a ValidationError.

**Validates: Requirements 2.3, 3.4, 9.4**

### Property 6: Network Device Update

For any existing network device and valid update data, updating the device shall result in the device record reflecting the new values for device type, device name, and IP address.

**Validates: Requirements 3.1, 3.5**

### Property 7: IP Release on Update and Delete

For any network device operation (IP change or deletion) that releases an IP address from a device, the old IP address shall be marked as free (is_assigned=False) after the operation completes.

**Validates: Requirements 3.2, 4.2**

### Property 8: Network Device Deletion

For any network device in the system, deleting the device shall result in the device record no longer existing in the database.

**Validates: Requirements 4.1**

### Property 9: IP Occupancy Display

For any IP address occupied by a network device, querying the IP management system shall return the IP as occupied with the associated device information.

**Validates: Requirements 5.1**

### Property 10: Search by IP Address

For any IP address in the system, searching for that IP address (or a substring of it) shall return that IP address in the search results.

**Validates: Requirements 6.1, 6.5**

### Property 11: Search by Device Name

For any network device in the system, searching for the device name (or a case-insensitive substring of it) shall return the device's IP address in the search results.

**Validates: Requirements 6.2, 6.4, 6.5**

### Property 12: Search by Asset Assigned Person

For any asset with an assigned person, searching for the assigned person name (or a case-insensitive substring of it) shall return the asset's IP address in the search results.

**Validates: Requirements 6.3, 6.5**

### Property 13: Device List Display Content

For any network device in the system, the device list view shall include the device's type, name, and IP address.

**Validates: Requirements 7.2**

### Property 14: Asset Export Exclusion

For any asset export operation, the exported data shall not include any network device records.

**Validates: Requirements 9.2**

### Property 15: Asset Search Exclusion

For any search query in the asset search functionality, the search results shall not include network device records.

**Validates: Requirements 9.3**

### Property 16: IP Address Format Validation

For any IP address value provided for a network device, the system shall validate that it conforms to valid IPv4 format, and invalid formats shall raise a ValidationError.

**Validates: Requirements 10.1, 10.2, 10.3**

## Error Handling

### Validation Errors

The system shall handle the following validation errors gracefully:

1. **IP Address Already Assigned**: When attempting to create or update a network device with an IP already assigned to another device or asset
   - Error: `ValidationError({'ip_address': 'IP address already in use'})`
   - User feedback: Display error message on form field
   - Recovery: User selects different IP address

2. **Invalid IP Address Format**: When IP address does not conform to IPv4 format
   - Error: `ValidationError({'ip_address': 'Enter a valid IPv4 address'})`
   - User feedback: Display error message on form field
   - Recovery: User enters valid IP address

3. **Missing Required Fields**: When device type, device name, or IP address is not provided
   - Error: `ValidationError({'field_name': 'This field is required'})`
   - User feedback: Display error message on form field
   - Recovery: User provides required information

4. **IP Address Not Found**: When attempting to assign non-existent IP address
   - Error: `ValidationError({'ip_address': 'Invalid IP address'})`
   - User feedback: Display error message on form field
   - Recovery: User selects valid IP from dropdown

### Database Errors

1. **Integrity Constraint Violation**: When database constraints are violated (e.g., unique constraint on IP address)
   - Handling: Catch IntegrityError, convert to ValidationError with user-friendly message
   - Rollback: Transaction automatically rolled back
   - User feedback: Display error message

2. **Foreign Key Constraint**: When attempting to delete IP address that has network device
   - Prevention: Use PROTECT on_delete to prevent deletion
   - Error: `ProtectedError`
   - User feedback: "Cannot delete IP address - it is assigned to a network device"

### Permission Errors

1. **Unauthorized Access**: When non-admin user attempts to access network device management
   - Handling: AdminRequiredMixin redirects to login page
   - User feedback: Login prompt or permission denied message

### Transaction Management

All create, update, and delete operations use Django's `transaction.atomic()` to ensure:
- All database changes succeed or all are rolled back
- IP assignment/release is atomic with device creation/update/deletion
- No partial state changes on error

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized test data

### Property-Based Testing

Property-based tests will be implemented using Hypothesis (Python's property-based testing library). Each correctness property will be implemented as a property-based test with minimum 100 iterations.

**Test Configuration**:
```python
from hypothesis import given, settings
from hypothesis import strategies as st

@settings(max_examples=100)
@given(
    device_type=st.sampled_from(['Camera', 'Printer', 'Punching Machine', 'Mobile', 'Other']),
    device_name=st.text(min_size=1, max_size=255),
    # ... other strategies
)
def test_property_X(device_type, device_name, ...):
    """Feature: network-device-tracking, Property X: [property text]"""
    # Test implementation
```

**Property Test Tags**: Each property test must include a comment tag:
```python
"""Feature: network-device-tracking, Property 1: Complete Device Data Storage"""
```

### Unit Testing

Unit tests will focus on:

1. **Specific Examples**:
   - Creating a camera device with specific IP
   - Updating a printer device's name
   - Deleting a punching machine device

2. **Edge Cases**:
   - Device name with special characters
   - Device name at maximum length (255 characters)
   - Last available IP address in a range

3. **Error Conditions**:
   - Attempting to create device with already-assigned IP
   - Attempting to update device with invalid IP format
   - Attempting to delete non-existent device

4. **Integration Points**:
   - IP assignment integration with IPManagementService
   - Free IPs page display with network devices
   - Search functionality across assets and network devices

### Test Coverage Goals

- **Model tests**: 100% coverage of NetworkDevice model methods
- **Service tests**: 100% coverage of NetworkDeviceService methods
- **View tests**: Coverage of all CRUD operations and error paths
- **Form tests**: Coverage of validation logic and field requirements
- **Integration tests**: Coverage of IP management integration and Free IPs page

### Test Data Generation

Property-based tests will use Hypothesis strategies to generate:
- Valid device types from predefined choices
- Device names of varying lengths and character sets
- Valid and invalid IP addresses
- Combinations of assigned and unassigned IPs

### Continuous Testing

- All tests run on every commit via CI/CD pipeline
- Property-based tests use consistent random seed for reproducibility
- Failed property tests provide minimal failing example for debugging
- Test database isolated from development and production databases

