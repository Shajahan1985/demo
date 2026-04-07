# Bugfix Requirements Document

## Introduction

When editing a laptop or All-in-One PC asset through the asset update form, the hardware serial number field value disappears and is not preserved during the update operation. This occurs because the `AssetUpdateView.form_valid()` method in `assets/views.py` does not include the `hardware_serial_number` field in the data dictionary passed to `AssetService.update_asset()`. This results in data loss for a critical field that is required for these asset types.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN editing a laptop asset with an existing hardware serial number THEN the system loses the hardware serial number value during the update operation

1.2 WHEN editing an All-in-One PC asset with an existing hardware serial number THEN the system loses the hardware serial number value during the update operation

1.3 WHEN submitting the asset update form with a hardware serial number value THEN the system does not pass the hardware_serial_number field to the AssetService.update_asset() method

### Expected Behavior (Correct)

2.1 WHEN editing a laptop asset with an existing hardware serial number THEN the system SHALL preserve the hardware serial number value during the update operation

2.2 WHEN editing an All-in-One PC asset with an existing hardware serial number THEN the system SHALL preserve the hardware serial number value during the update operation

2.3 WHEN submitting the asset update form with a hardware serial number value THEN the system SHALL pass the hardware_serial_number field to the AssetService.update_asset() method

### Unchanged Behavior (Regression Prevention)

3.1 WHEN editing a desktop asset without a hardware serial number THEN the system SHALL CONTINUE TO update the asset without requiring a hardware serial number

3.2 WHEN editing a server asset without a hardware serial number THEN the system SHALL CONTINUE TO update the asset without requiring a hardware serial number

3.3 WHEN creating a new laptop asset with a hardware serial number THEN the system SHALL CONTINUE TO save the hardware serial number correctly

3.4 WHEN editing any asset type and updating other fields (asset_tag, manufacturer, operating_system, etc.) THEN the system SHALL CONTINUE TO update those fields correctly

3.5 WHEN editing an asset with manual IP entry THEN the system SHALL CONTINUE TO handle manual IP addresses correctly

3.6 WHEN editing an asset with manual OS entry THEN the system SHALL CONTINUE TO handle manual operating system entries correctly
