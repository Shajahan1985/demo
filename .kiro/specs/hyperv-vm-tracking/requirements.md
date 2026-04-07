# Requirements Document

## Introduction

This feature extends the Django Asset Tracker application to support tracking Hyper-V virtual machines (VMs) and their relationship to physical host machines. The system will track VM details, IP addresses, and maintain bidirectional relationships between VMs and their hosts. The feature includes IP range-specific behavior to accommodate different VM usage patterns across network segments.

## Glossary

- **Asset_Tracker**: The Django application that manages IT assets
- **Hyper_V_VM**: A virtual machine running on Microsoft Hyper-V hypervisor
- **Host_Machine**: A physical Asset that hosts one or more Hyper-V VMs
- **VM_Relationship**: The bidirectional link between a Hyper-V VM and its Host Machine
- **IP_Management_System**: The existing system that tracks IP addresses and their assignment status
- **VM_IP_Address**: An IP address assigned to a Hyper-V VM
- **IP_Range**: A network segment defined by a pattern (e.g., 192.168.50.x)
- **Common_VM_Range**: IP ranges where Hyper-V VMs are frequently used (192.168.50.x)
- **Rare_VM_Range**: IP ranges where Hyper-V VMs are infrequently used (192.168.10.x, 192.168.11.x, 192.168.70.x)
- **Asset_Detail_View**: The page displaying detailed information about a specific Asset
- **IP_Status_Display**: Visual representation of IP address availability (red for occupied, green for free)

## Requirements

### Requirement 1: Track Hyper-V Virtual Machines

**User Story:** As a system administrator, I want to track Hyper-V virtual machines with their details, so that I can maintain an inventory of all VMs in the infrastructure.

#### Acceptance Criteria

1. THE Asset_Tracker SHALL store Hyper-V VM records with name, IP address, and host machine reference
2. THE Asset_Tracker SHALL provide a dedicated form specifically for entering Hyper-V VM details
3. THE Asset_Tracker SHALL allow creation of Hyper-V VM records through the dedicated VM entry form
4. THE Asset_Tracker SHALL allow editing of existing Hyper-V VM records
5. THE Asset_Tracker SHALL allow deletion of Hyper-V VM records
6. WHEN a Hyper-V VM is created, THE Asset_Tracker SHALL validate that all required fields are provided
7. THE Asset_Tracker SHALL display a list of all Hyper-V VMs with their details

### Requirement 2: Link VMs to Host Machines

**User Story:** As a system administrator, I want to link virtual machines to their physical host machines, so that I can understand the infrastructure topology.

#### Acceptance Criteria

1. WHEN creating a Hyper-V VM through the dedicated VM entry form, THE Asset_Tracker SHALL require selection of a Host Machine by its IP address
2. THE Asset_Tracker SHALL display available Host Machine IP addresses for selection during VM creation
3. THE Asset_Tracker SHALL maintain a bidirectional relationship between Hyper-V VMs and Host Machines
4. WHEN a Host Machine is deleted, THE Asset_Tracker SHALL prevent deletion if it has associated Hyper-V VMs
5. THE Asset_Tracker SHALL allow reassignment of a Hyper-V VM to a different Host Machine
6. FOR ALL Hyper-V VMs, THE Asset_Tracker SHALL ensure the Host Machine reference remains valid

### Requirement 3: Display Host Machine's VMs

**User Story:** As a system administrator, I want to see all virtual machines hosted on a physical machine, so that I can understand the host's workload.

#### Acceptance Criteria

1. WHEN viewing a Host Machine's Asset_Detail_View, THE Asset_Tracker SHALL display a list of all its Hyper-V VMs
2. FOR EACH Hyper-V VM in the list, THE Asset_Tracker SHALL display the VM name and IP address
3. THE Asset_Tracker SHALL display the VM list in a dedicated section on the Host Machine's detail page
4. WHEN a Host Machine has no Hyper-V VMs, THE Asset_Tracker SHALL display an appropriate message
5. THE Asset_Tracker SHALL provide clickable links from the VM list to individual VM detail pages
6. WHEN viewing the IP list page for a Host Machine IP address, THE Asset_Tracker SHALL display all Hyper-V VM IP addresses hosted on that machine
7. THE Asset_Tracker SHALL provide clickable links from Host Machine IPs to their associated VM IPs in the IP list view

### Requirement 4: Display VM's Host Machine

**User Story:** As a system administrator, I want to see which physical machine hosts a virtual machine, so that I can locate the VM's infrastructure.

#### Acceptance Criteria

1. WHEN viewing a Hyper-V VM's detail page, THE Asset_Tracker SHALL display its Host Machine name
2. WHEN viewing a Hyper-V VM's detail page, THE Asset_Tracker SHALL display its Host Machine IP address
3. THE Asset_Tracker SHALL provide a clickable link from the VM detail page to the Host Machine's Asset_Detail_View
4. THE Asset_Tracker SHALL display the Host Machine information in a dedicated section on the VM detail page
5. WHEN viewing the IP list page for a VM IP address, THE Asset_Tracker SHALL display the base machine IP address that hosts this VM
6. THE Asset_Tracker SHALL provide a clickable link from VM IPs to their Host Machine IP in the IP list view

### Requirement 5: Display Bidirectional VM-Host Relationships in IP List

**User Story:** As a system administrator, I want to see VM-host relationships directly in the IP list page, so that I can quickly understand the infrastructure topology without navigating to detail pages.

#### Acceptance Criteria

1. WHEN viewing the IP list page, THE Asset_Tracker SHALL display bidirectional relationships between Host Machine IPs and VM IPs
2. FOR EACH Host Machine IP in the list, THE Asset_Tracker SHALL show all Hyper-V VM IPs hosted on that machine
3. FOR EACH VM IP in the list, THE Asset_Tracker SHALL show its base machine IP address
4. THE Asset_Tracker SHALL provide clickable links between related IPs in the IP list view
5. WHEN a Host Machine has no VMs, THE Asset_Tracker SHALL display the Host Machine IP without VM relationship indicators
6. WHEN viewing a VM IP, THE Asset_Tracker SHALL clearly indicate which IP is the host machine

### Requirement 6: Mark VM IP Addresses as Occupied

**User Story:** As a system administrator, I want VM IP addresses to show as occupied in IP management, so that I can avoid IP address conflicts.

#### Acceptance Criteria

1. WHEN a Hyper-V VM is assigned an IP address, THE IP_Management_System SHALL mark that IP address as occupied
2. WHEN displaying IP addresses, THE IP_Management_System SHALL show VM-occupied IPs with red color
3. WHEN hovering over a VM-occupied IP address, THE IP_Management_System SHALL display the VM name and host machine
4. WHEN a Hyper-V VM is deleted, THE IP_Management_System SHALL mark its IP address as free
5. WHEN a Hyper-V VM's IP address is changed, THE IP_Management_System SHALL mark the old IP as free and the new IP as occupied

### Requirement 7: IP Range-Specific VM Options

**User Story:** As a system administrator, I want different VM creation options based on IP range, so that the interface reflects actual VM usage patterns.

#### Acceptance Criteria

1. WHERE an IP address belongs to a Common_VM_Range, THE Asset_Tracker SHALL prominently display the option to create a Hyper-V VM
2. WHERE an IP address belongs to a Rare_VM_Range, THE Asset_Tracker SHALL display the option to create a Hyper-V VM with lower prominence
3. THE Asset_Tracker SHALL identify 192.168.50.x as a Common_VM_Range
4. THE Asset_Tracker SHALL identify 192.168.10.x, 192.168.11.x, and 192.168.70.x as Rare_VM_Ranges
5. WHEN displaying IP addresses in the IP_Management_System, THE Asset_Tracker SHALL apply range-specific UI styling

### Requirement 8: Validate VM IP Addresses

**User Story:** As a system administrator, I want to ensure VM IP addresses are valid and not duplicated, so that the network configuration remains consistent.

#### Acceptance Criteria

1. WHEN creating a Hyper-V VM, THE Asset_Tracker SHALL validate that the IP address is a valid IPv4 address
2. WHEN creating a Hyper-V VM, THE Asset_Tracker SHALL validate that the IP address is not already assigned to another VM or Asset
3. IF a duplicate IP address is provided, THEN THE Asset_Tracker SHALL display an error message and prevent VM creation
4. THE Asset_Tracker SHALL allow a Hyper-V VM to have no IP address assigned
5. WHEN editing a Hyper-V VM, THE Asset_Tracker SHALL apply the same IP validation rules as creation

### Requirement 9: VM Lifecycle Management

**User Story:** As a system administrator, I want to manage the lifecycle of virtual machines, so that I can track VMs from creation to decommissioning.

#### Acceptance Criteria

1. WHEN a Hyper-V VM is created, THE Asset_Tracker SHALL record the creation timestamp
2. WHEN a Hyper-V VM is modified, THE Asset_Tracker SHALL record the modification timestamp
3. THE Asset_Tracker SHALL allow marking a Hyper-V VM as inactive without deleting it
4. WHEN a Hyper-V VM is marked as inactive, THE Asset_Tracker SHALL release its IP address
5. THE Asset_Tracker SHALL maintain a history of all Hyper-V VMs including inactive ones

### Requirement 10: Search and Filter VMs

**User Story:** As a system administrator, I want to search and filter virtual machines, so that I can quickly find specific VMs.

#### Acceptance Criteria

1. THE Asset_Tracker SHALL provide a search function for Hyper-V VMs by name
2. THE Asset_Tracker SHALL provide a filter for Hyper-V VMs by Host Machine
3. THE Asset_Tracker SHALL provide a filter for Hyper-V VMs by IP range
4. WHEN search or filter criteria are applied, THE Asset_Tracker SHALL display only matching Hyper-V VMs
5. THE Asset_Tracker SHALL display the count of filtered results

### Requirement 11: VM Data Integrity

**User Story:** As a system administrator, I want to ensure VM data remains consistent, so that the inventory is reliable.

#### Acceptance Criteria

1. WHEN a Host Machine's IP address changes, THE Asset_Tracker SHALL maintain the VM relationships
2. WHEN a Host Machine is updated, THE Asset_Tracker SHALL preserve all associated VM records
3. FOR ALL Hyper-V VMs, parsing the VM record then serializing it then parsing again SHALL produce an equivalent VM record (round-trip property)
4. THE Asset_Tracker SHALL prevent creation of circular VM-host relationships
5. WHEN database operations fail, THE Asset_Tracker SHALL rollback all changes to maintain data consistency
