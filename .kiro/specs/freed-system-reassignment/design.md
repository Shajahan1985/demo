# Design Document: Freed System Reassignment

## Overview

The Freed System Reassignment feature enables administrators to transition healthy freed systems back to active status by reassigning them to new users and teams. This feature extends the existing asset lifecycle management system by adding a reassignment workflow that handles status transitions, IP address management, and validation.

The feature integrates with the existing freed systems page, adding a "Reassign" action for healthy systems. When an administrator initiates reassignment, they provide the new user, team, and IP address through a form. The system validates the inputs, transitions the asset from freed to active status, manages IP address allocation, and provides feedback on success or failure.

Key design goals:
- Maintain data integrity through atomic transactions
- Reuse existing IP management infrastructure
- Provide clear validation feedback
- Ensure only healthy freed systems can be reassigned
- Preserve audit trail through proper field management

## Architecture

The reassignment feature follows the existing Django MVC architecture with service layer pattern:

```
┌─────────────────┐
│  Template Layer │  freed_systems.html (add Reassign button)
│                 │  asset_reassign_form.html (new)
└────────┬────────┘
         │
┌────────▼────────┐
│   View Layer    │  AssetReassignView (new)
└────────┬────────┘
         │
┌────────▼────────┐
│  Service Layer  │  AssetService.reassign_asset() (new)
│                 │  IPManagementService (existing)
└────────┬────────┘
         │
┌────────▼────────┐
│   Model Layer   │  Asset, IPAddress, Team (existing)
└─────────────────┘
```

The design leverages existing components:
- IPManagementService for IP allocation/release
- AssetService for asset operations
- Team model with hierarchical support
- Asset model with status field

New components:
- AssetReassignView: Handles GET (display form) and POST (process reassignment)
- ReassignmentForm: Validates reassignment inputs
- AssetService.reassign_asset(): Orchestrates the reassignment transaction

## Components and Interfaces

### 1. AssetReassignView

**Purpose**: Handle reassignment form display and submission

**Methods**:
- `get(request, pk)`: Display reassignment form for freed asset
- `post(request, pk)`: Process reassignment submission
- `get_context_data()`: Provide asset details and form to template

**Inputs**:
- URL parameter: asset pk
- POST data: assigned_to, team, ip_address, manual_ip

**Outputs**:
- Success: Redirect to active assets page with success message
- Failure: Re-render form with validation errors

**Permissions**: AdminRequiredMixin (is_staff=True)

### 2. ReassignmentForm

**Purpose**: Validate reassignment inputs

**Fields**:
- `assigned_to`: CharField (required)
- `team`: ModelChoiceField (required, hierarchical display)
- `ip_address`: ModelChoiceField (optional, filtered to is_assigned=False)
- `manual_ip`: GenericIPAddressField (optional)

**Validation**:
- At least one of ip_address or manual_ip must be provided
- If ip_address selected, must have is_assigned=False
- manual_ip must be valid IPv4 format
- Cannot provide both ip_address and manual_ip

**Methods**:
- `clean()`: Cross-field validation for IP selection
- `clean_manual_ip()`: Validate IP format

### 3. AssetService.reassign_asset()

**Purpose**: Execute atomic reassignment transaction

**Signature**:
```python
@staticmethod
def reassign_asset(asset, data, user):
    """
    Reassign freed asset to active status.
    
    Args:
        asset: Asset instance to reassign
        data: Dict with keys: assigned_to, team, ip_address_id, manual_ip
        user: User performing reassignment
    
    Returns:
        Asset: Updated asset instance
    
    Raises:
        ValidationError: If validation fails
    """
```

**Transaction Steps**:
1. Validate asset status is 'freed'
2. Validate asset health_status is 'healthy'
3. Release old IP if exists (set is_assigned=False, assigned_to_asset=None)
4. Assign new IP if ip_address_id provided
5. Update asset fields:
   - status = 'active'
   - assigned_to = data['assigned_to']
   - team_id = data['team']
   - freed_date = None
   - health_status = None
   - issues_description = None
   - ip_address or manual_ip based on selection
6. Save asset

**Error Handling**:
- Wrap in transaction.atomic()
- Raise ValidationError for business rule violations
- Let database errors propagate for rollback

### 4. Template Updates

**freed_systems.html**:
- Add conditional "Reassign" button for each freed asset
- Condition: `{% if asset.health_status == 'healthy' and user.is_staff %}`
- Button links to: `{% url 'asset_reassign' asset.pk %}`

**asset_reassign_form.html** (new):
- Display asset details (read-only): asset_tag, system_type, operating_system
- Render ReassignmentForm fields
- Include JavaScript for IP selection toggle (dropdown vs manual)
- Submit button: "Reassign Asset"
- Cancel button: Return to freed systems page

### 5. URL Configuration

Add to assets/urls.py:
```python
path('<int:pk>/reassign/', AssetReassignView.as_view(), name='asset_reassign'),
```

## Data Models

No new models required. The feature uses existing models:

### Asset Model (existing)

Relevant fields for reassignment:
- `status`: CharField (active/freed/scrapped) - transitions from 'freed' to 'active'
- `health_status`: CharField (healthy/defective) - must be 'healthy' to reassign
- `assigned_to`: CharField - set to new user name
- `team`: ForeignKey(Team) - set to selected team
- `freed_date`: DateTimeField - cleared on reassignment
- `issues_description`: TextField - cleared on reassignment
- `ip_address`: ForeignKey(IPAddress) - set if dropdown IP selected
- `manual_ip`: GenericIPAddressField - set if manual IP provided

### IPAddress Model (existing)

Relevant fields:
- `is_assigned`: BooleanField - updated during IP management
- `assigned_to_asset`: ForeignKey(Asset) - updated during IP management
- `freed_date`: DateTimeField - set when IP released

### Team Model (existing)

Used for team selection dropdown with hierarchical display via `Team.objects.get_hierarchical_choices()`

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Reassign button visibility for healthy systems

*For any* freed asset with health_status='healthy' and any administrator user, the freed systems page should display a "Reassign" button for that asset.

**Validates: Requirements 1.1**

### Property 2: Reassign button hidden for non-administrators

*For any* freed asset and any non-administrator user, the freed systems page should not display any "Reassign" buttons.

**Validates: Requirements 1.3**

### Property 3: IP dropdown contains only unassigned IPs

*For any* reassignment form display, the IP Address dropdown should contain only IPAddress records where is_assigned=False.

**Validates: Requirements 2.4, 2.7**

### Property 4: Empty assigned_to validation

*For any* reassignment submission where the assigned_to field is empty or contains only whitespace, the service should return a validation error.

**Validates: Requirements 3.1**

### Property 5: Assigned IP validation

*For any* reassignment submission with an IP Address where is_assigned=True, the service should return a validation error.

**Validates: Requirements 3.4**

### Property 6: Health status validation

*For any* asset where health_status is not 'healthy', attempting reassignment should return a validation error.

**Validates: Requirements 3.5**

### Property 7: Asset status validation

*For any* asset where status is not 'freed', attempting reassignment should return a validation error.

**Validates: Requirements 3.6**

### Property 8: Complete state transition on reassignment

*For any* valid reassignment with data (assigned_to, team, ip_address or manual_ip), the reassigned asset should have: status='active', assigned_to matching input, team matching input, freed_date=None, health_status=None, and issues_description=None.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

### Property 9: Dropdown IP assignment

*For any* reassignment using an IP Address from the dropdown, the result should have: the IPAddress.is_assigned=True, IPAddress.assigned_to_asset pointing to the asset, asset.ip_address pointing to the IPAddress, and asset.manual_ip=None.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 10: Old IP release

*For any* freed asset with an existing ip_address, when reassignment occurs, the old IPAddress should have is_assigned=False and assigned_to_asset=None.

**Validates: Requirements 5.5, 5.6, 6.3, 6.4**

### Property 11: Manual IP assignment

*For any* reassignment using a manual IP value, the result should have: asset.manual_ip set to the provided IP address and asset.ip_address=None.

**Validates: Requirements 6.1, 6.2**

### Property 12: Manual IP format validation

*For any* reassignment submission with an invalid IPv4 format in manual_ip, the service should return a validation error.

**Validates: Requirements 6.5**

### Property 13: Freed systems page filtering

*For any* freed systems page load, the displayed assets should only include assets where status='freed'.

**Validates: Requirements 7.1, 7.2**

### Property 14: Free IPs page reflects assignment status

*For any* Free IPs page load, IPAddress records with is_assigned=True should display as occupied, and records with is_assigned=False should display as unoccupied.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 15: Manual IPs shown as occupied

*For any* Free IPs page load, manual IP addresses from active assets should display as occupied.

**Validates: Requirements 8.5**

### Property 16: Success message contains asset tag

*For any* successful reassignment, the success message should contain the asset_tag of the reassigned asset.

**Validates: Requirements 9.2, 9.3**

### Property 17: Transaction atomicity on failure

*For any* reassignment attempt that fails validation or encounters a database error, all database changes should be rolled back and the asset should retain its original status, assigned_to, team, freed_date, health_status, issues_description, and IP assignments.

**Validates: Requirements 10.2, 10.3, 10.4**

## Error Handling

The reassignment feature implements comprehensive error handling at multiple layers:

### Validation Errors

**Form-level validation**:
- Empty required fields (assigned_to, team)
- Missing IP selection (both ip_address and manual_ip empty)
- Invalid IP format for manual_ip
- Errors displayed inline with form fields

**Service-level validation**:
- Asset status must be 'freed'
- Asset health_status must be 'healthy'
- Selected IP must have is_assigned=False
- Validation errors raised as Django ValidationError with field-specific messages

### Database Errors

**Transaction management**:
- All reassignment operations wrapped in `transaction.atomic()`
- Database errors trigger automatic rollback
- Original asset state preserved on failure
- Error messages logged for debugging

### Permission Errors

**Access control**:
- AdminRequiredMixin enforces is_staff=True
- Non-admin users receive 403 Forbidden response
- Reassign buttons hidden from non-admin users in UI

### User Feedback

**Success scenarios**:
- Redirect to active assets page
- Success message: "Asset {asset_tag} has been reassigned and is now active"

**Failure scenarios**:
- Re-render form with validation errors highlighted
- Error messages displayed at field level and form level
- Original form data preserved for correction

### Edge Cases

**IP address conflicts**:
- If selected IP becomes assigned between form display and submission, validation error returned
- User prompted to select different IP

**Concurrent modifications**:
- If asset status changes between form display and submission, validation error returned
- User redirected to freed systems page to see current state

**Missing related objects**:
- If selected team or IP is deleted before submission, validation error returned
- Form re-rendered with updated dropdown options

## Testing Strategy

The freed system reassignment feature requires both unit testing and property-based testing to ensure correctness across all scenarios.

### Property-Based Testing

Property-based testing will be implemented using **Hypothesis** (Python's property-based testing library). Each correctness property will be tested with a minimum of 100 iterations to ensure comprehensive input coverage.

**Test configuration**:
```python
from hypothesis import given, settings
from hypothesis import strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Feature: freed-system-reassignment, Property N: [property text]
    pass
```

**Property test coverage**:
- Property 1: Generate freed assets with various health statuses, verify button visibility
- Property 2: Generate user objects with different permission levels, verify button hiding
- Property 3: Generate IP addresses with various assignment states, verify dropdown filtering
- Property 4: Generate empty/whitespace strings, verify validation rejection
- Property 5: Generate assigned IPs, verify validation rejection
- Property 6: Generate assets with various health statuses, verify validation
- Property 7: Generate assets with various statuses, verify validation
- Property 8: Generate valid reassignment data, verify complete state transition
- Property 9: Generate dropdown IP selections, verify IP assignment behavior
- Property 10: Generate assets with existing IPs, verify old IP release
- Property 11: Generate manual IP values, verify manual IP assignment
- Property 12: Generate invalid IP formats, verify validation rejection
- Property 13: Generate assets with various statuses, verify page filtering
- Property 14: Generate IP addresses with various states, verify page display
- Property 15: Generate active assets with manual IPs, verify page display
- Property 16: Generate successful reassignments, verify message content
- Property 17: Generate failing reassignments, verify rollback behavior

**Generator strategies**:
- Asset generators: Create assets with randomized fields (status, health_status, ip_address)
- IP generators: Create IPs with randomized assignment states
- Team generators: Create teams with hierarchical relationships
- User generators: Create users with randomized permission levels
- Form data generators: Create valid and invalid reassignment data

### Unit Testing

Unit tests will focus on specific examples, edge cases, and integration points:

**View layer tests**:
- GET request displays form with correct asset details
- POST request with valid data redirects to active assets page
- POST request with invalid data re-renders form with errors
- Non-admin users receive 403 response
- Invalid asset pk returns 404

**Service layer tests**:
- reassign_asset() with valid data updates all fields correctly
- reassign_asset() with invalid asset status raises ValidationError
- reassign_asset() with invalid health status raises ValidationError
- reassign_asset() with assigned IP raises ValidationError
- reassign_asset() releases old IP when present
- reassign_asset() handles dropdown IP selection
- reassign_asset() handles manual IP entry
- reassign_asset() rolls back on validation error
- reassign_asset() rolls back on database error (simulated)

**Form layer tests**:
- Form validates required fields (assigned_to, team)
- Form validates at least one IP field provided
- Form validates IP format for manual_ip
- Form rejects both ip_address and manual_ip provided
- Form populates IP dropdown with only unassigned IPs
- Form displays team dropdown in hierarchical format

**Integration tests**:
- End-to-end reassignment flow from freed systems page to active assets page
- IP address state changes reflected on Free IPs page
- Reassigned asset disappears from freed systems page
- Reassigned asset appears on active assets page with correct details

**Edge case tests**:
- Reassignment with asset that has no previous IP
- Reassignment with asset that has previous dropdown IP
- Reassignment with asset that has previous manual IP
- Concurrent reassignment attempts (simulate with database locks)
- Form submission with deleted team (should show validation error)
- Form submission with deleted IP (should show validation error)

### Test Data Management

**Fixtures**:
- Create base fixtures for teams, operating systems, IP ranges
- Use factory pattern for generating test assets and IPs
- Isolate tests with database transactions (Django TestCase)

**Mocking**:
- Mock user authentication for permission tests
- Mock database errors for rollback tests
- Mock concurrent modifications for edge case tests

### Coverage Goals

- Line coverage: >90% for new code (views, forms, service methods)
- Branch coverage: >85% for conditional logic
- Property tests: 100% of correctness properties implemented
- Unit tests: All edge cases and error paths covered
