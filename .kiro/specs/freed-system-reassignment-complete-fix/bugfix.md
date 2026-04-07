# Bugfix Requirements Document

## Introduction

The freed system reassignment functionality is completely broken - when users attempt to reassign a healthy freed system back to active status, the form displays "processing" but never submits. This prevents freed systems from being reassigned, blocking the entire reassignment workflow. The root cause is that the JavaScript form validation prevents submission when the hidden team field is empty, but the hidden team field is not being properly populated when the user selects a team from the dropdown.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user selects a parent team from the dropdown THEN the hidden team field remains empty and form submission is blocked by JavaScript validation

1.2 WHEN a user selects a parent team and then a sub-team THEN the hidden team field may not update correctly and form submission is blocked

1.3 WHEN the form is submitted with an empty hidden team field THEN the JavaScript validation prevents submission and shows "processing" indefinitely without any error message

1.4 WHEN the user switches between manual IP entry and dropdown IP selection THEN the hidden team field state is not preserved correctly

### Expected Behavior (Correct)

2.1 WHEN a user selects a parent team from the dropdown THEN the hidden team field SHALL be immediately populated with the parent team ID

2.2 WHEN a user selects a sub-team after selecting a parent team THEN the hidden team field SHALL be updated to the sub-team ID

2.3 WHEN the form is submitted with all required fields filled THEN the form SHALL submit successfully without being blocked by JavaScript validation

2.4 WHEN the form submission is blocked due to validation errors THEN the system SHALL display a clear error message to the user explaining what needs to be corrected

2.5 WHEN the reassignment completes successfully THEN the asset SHALL move from freed status to active status and appear on the active systems page

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user selects an IP from the dropdown (not manual entry) THEN the system SHALL CONTINUE TO process the reassignment correctly

3.2 WHEN a user toggles between OS dropdown and manual OS entry THEN the system SHALL CONTINUE TO handle OS selection correctly

3.3 WHEN a user fills out other form fields (assigned_to, system_type, manufacturer, etc.) THEN the system SHALL CONTINUE TO accept and process these fields correctly

3.4 WHEN the form has validation errors from the backend THEN the system SHALL CONTINUE TO display those errors to the user

3.5 WHEN a freed system is not healthy THEN the system SHALL CONTINUE TO prevent reassignment with an appropriate error message
