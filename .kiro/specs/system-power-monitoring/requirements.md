# Requirements Document

## Introduction

The System Power Monitoring feature enables tracking and management of computer systems that remain powered on when not in use. The feature monitors system power status, displays systems left on with user and network information, provides remote shutdown capability, and sends email notifications to designated recipients. This helps reduce energy waste and enforce company power management policies while allowing exemptions for critical systems that must remain operational.

## Glossary

- **Power_Monitor**: The system component that detects and tracks the power status of computer systems
- **Asset**: A computer system tracked in the Asset Tracker application with properties including assigned user, IP address, and system type
- **Power_Status**: The current operational state of a system (online or offline)
- **Shutdown_Manager**: The component that executes remote shutdown commands on target systems
- **Notification_Service**: The component that sends email alerts about systems left powered on
- **Exempt_System**: A system designated as critical that should not be automatically shut down or flagged in reports
- **Power_Report_Page**: The web interface displaying systems currently powered on with user and network details
- **Monitoring_Schedule**: The configured time intervals when the system checks for powered-on systems
- **After_Hours_Cutoff**: The time threshold (default 8:30 PM) after which systems should be powered off
- **After_Hours_System**: A system that remains powered on after the After_Hours_Cutoff time

## Requirements

### Requirement 1: Monitor System Power Status

**User Story:** As a system administrator, I want to automatically detect which systems are currently powered on, so that I can identify systems left running unnecessarily.

#### Acceptance Criteria

1. THE Power_Monitor SHALL check the power status of all Assets at configured intervals
2. WHEN an Asset responds to a network connectivity check, THE Power_Monitor SHALL record the Power_Status as online
3. WHEN an Asset does not respond to a network connectivity check, THE Power_Monitor SHALL record the Power_Status as offline
4. THE Power_Monitor SHALL store the timestamp of the last status check for each Asset
5. THE Power_Monitor SHALL store the timestamp when each Asset's Power_Status last changed
6. WHERE an Asset is marked as an Exempt_System, THE Power_Monitor SHALL still track Power_Status but flag it as exempt

### Requirement 2: Display Powered-On Systems

**User Story:** As a system administrator, I want to view a list of systems currently powered on, so that I can identify which users have left their systems running.

#### Acceptance Criteria

1. THE Power_Report_Page SHALL display all Assets with Power_Status of online
2. FOR each online Asset, THE Power_Report_Page SHALL display the assigned user name
3. FOR each online Asset, THE Power_Report_Page SHALL display the IP address
4. FOR each online Asset, THE Power_Report_Page SHALL display the duration the system has been online
5. THE Power_Report_Page SHALL indicate which Assets are marked as Exempt_System
6. THE Power_Report_Page SHALL exclude Exempt_System Assets from the default view
7. WHERE a user requests to view exempt systems, THE Power_Report_Page SHALL display Exempt_System Assets in a separate section
8. THE Power_Report_Page SHALL refresh the displayed data when the user requests an update
9. WHEN the current time is after the After_Hours_Cutoff, THE Power_Report_Page SHALL highlight After_Hours_System Assets
10. THE Power_Report_Page SHALL provide a filter to show only After_Hours_System Assets

### Requirement 3: Remote System Shutdown

**User Story:** As a system administrator, I want to remotely shut down systems that are left powered on, so that I can enforce power management policies without physically visiting each system.

#### Acceptance Criteria

1. WHEN an administrator selects an Asset for shutdown, THE Shutdown_Manager SHALL send a shutdown command to the Asset's IP address
2. THE Shutdown_Manager SHALL verify the administrator has permission to execute shutdown commands before proceeding
3. WHERE an Asset is marked as an Exempt_System, THE Shutdown_Manager SHALL prevent shutdown and display a warning message
4. WHEN a shutdown command is sent, THE Shutdown_Manager SHALL log the action with timestamp, administrator identity, and target Asset
5. IF a shutdown command fails, THEN THE Shutdown_Manager SHALL record the failure reason and notify the administrator
6. WHEN a shutdown command succeeds, THE Shutdown_Manager SHALL update the Asset's Power_Status to offline
7. THE Shutdown_Manager SHALL provide a bulk shutdown option to shut down multiple non-exempt Assets simultaneously

### Requirement 4: Email Notifications for Powered-On Systems

**User Story:** As a manager, I want to receive email notifications about systems left powered on after hours, so that I can follow up with users about power management compliance.

#### Acceptance Criteria

1. WHEN the Monitoring_Schedule triggers a notification check, THE Notification_Service SHALL identify all non-exempt Assets with Power_Status of online
2. WHERE online Assets are detected during a notification check, THE Notification_Service SHALL send an email to all configured recipients
3. THE Notification_Service SHALL include the user name for each online Asset in the email
4. THE Notification_Service SHALL include the IP address for each online Asset in the email
5. THE Notification_Service SHALL include the duration each Asset has been online in the email
6. THE Notification_Service SHALL format the email with a clear subject line indicating systems left powered on
7. THE Notification_Service SHALL send emails only during configured notification windows to avoid off-hours alerts
8. WHEN the current time is after the After_Hours_Cutoff, THE Notification_Service SHALL prioritize After_Hours_System Assets in the email notification
9. THE Notification_Service SHALL clearly indicate in the email which systems are powered on after the After_Hours_Cutoff time

### Requirement 5: Configure Email Recipients

**User Story:** As a system administrator, I want to configure which email addresses receive power monitoring notifications, so that I can control who is informed about power management issues.

#### Acceptance Criteria

1. THE Notification_Service SHALL maintain a list of email recipient addresses
2. THE Notification_Service SHALL support multiple email recipients for each notification
3. WHEN an administrator adds an email address, THE Notification_Service SHALL validate the email format before saving
4. WHEN an administrator removes an email address, THE Notification_Service SHALL remove it from the recipient list
5. THE Notification_Service SHALL provide a default recipient address of shajahan.t@benzyinfotech.com
6. WHERE no recipients are configured, THE Notification_Service SHALL use the default recipient address
7. THE Notification_Service SHALL allow administrators to enable or disable individual recipients without deleting them

### Requirement 6: Manage Exempt Systems

**User Story:** As a system administrator, I want to designate certain systems as exempt from shutdown and notifications, so that critical systems remain operational without triggering alerts.

#### Acceptance Criteria

1. THE Power_Monitor SHALL allow administrators to mark any Asset as an Exempt_System
2. THE Power_Monitor SHALL allow administrators to remove the Exempt_System designation from any Asset
3. WHEN an Asset is marked as an Exempt_System, THE Power_Monitor SHALL record the reason for exemption
4. WHEN an Asset is marked as an Exempt_System, THE Power_Monitor SHALL record which administrator created the exemption
5. THE Power_Report_Page SHALL clearly indicate which Assets are designated as Exempt_System
6. THE Notification_Service SHALL exclude Exempt_System Assets from email notifications
7. THE Shutdown_Manager SHALL prevent shutdown operations on Exempt_System Assets

### Requirement 7: Configure Monitoring Schedule

**User Story:** As a system administrator, I want to configure when the system checks for powered-on systems, so that monitoring aligns with business hours and power management policies.

#### Acceptance Criteria

1. THE Power_Monitor SHALL allow administrators to configure the interval between power status checks
2. THE Power_Monitor SHALL allow administrators to configure specific times when notification emails are sent
3. THE Power_Monitor SHALL validate that configured check intervals are between 1 minute and 24 hours
4. WHEN the configured check interval elapses, THE Power_Monitor SHALL execute a power status check for all Assets
5. WHEN the configured notification time is reached, THE Notification_Service SHALL check for online Assets and send emails if any are found
6. THE Power_Monitor SHALL provide a default check interval of 15 minutes
7. THE Notification_Service SHALL provide a default notification time at the end of the business day

### Requirement 8: Monitor After-Hours System Usage

**User Story:** As a system administrator, I want to identify systems that remain powered on after 8:30 PM, so that I can enforce after-hours power management policies and reduce energy waste.

#### Acceptance Criteria

1. THE Power_Monitor SHALL allow administrators to configure the After_Hours_Cutoff time
2. THE Power_Monitor SHALL provide a default After_Hours_Cutoff time of 8:30 PM
3. WHEN the current time exceeds the After_Hours_Cutoff, THE Power_Monitor SHALL identify all non-exempt Assets with Power_Status of online as After_Hours_System Assets
4. THE Power_Report_Page SHALL display a dedicated section showing only After_Hours_System Assets
5. FOR each After_Hours_System, THE Power_Report_Page SHALL display how long the system has been on past the After_Hours_Cutoff
6. THE Notification_Service SHALL send a specific email notification when After_Hours_System Assets are detected
7. THE Notification_Service SHALL schedule the after-hours notification check to run shortly after the After_Hours_Cutoff time
8. WHERE an Asset becomes online after the After_Hours_Cutoff, THE Power_Monitor SHALL immediately flag it as an After_Hours_System

### Requirement 9: Audit Logging

**User Story:** As a system administrator, I want to review a history of power monitoring actions, so that I can audit system usage and administrative actions.

#### Acceptance Criteria

1. THE Power_Monitor SHALL log each power status change for every Asset with timestamp
2. THE Shutdown_Manager SHALL log each shutdown command with timestamp, administrator identity, target Asset, and result
3. THE Notification_Service SHALL log each email notification sent with timestamp, recipient list, and number of Assets reported
4. WHEN an administrator marks or unmarks an Asset as an Exempt_System, THE Power_Monitor SHALL log the action with timestamp and administrator identity
5. THE Power_Report_Page SHALL provide access to view audit logs filtered by date range
6. THE Power_Report_Page SHALL provide access to view audit logs filtered by Asset
7. THE Power_Report_Page SHALL provide access to view audit logs filtered by action type
