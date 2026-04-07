# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Hardware Serial Number Loss on Laptop/All-in-One PC Edit
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: laptop/All-in-One PC assets with existing hardware serial numbers being edited
  - Test that editing a laptop asset with hardware serial number "ABC123" and changing it to "XYZ789" results in the hardware_serial_number field being updated to "XYZ789" (from Bug Condition in design)
  - Test that editing an All-in-One PC asset with hardware serial number "DEF456" while changing the manufacturer preserves the hardware serial number "DEF456"
  - Test that the data dictionary passed to AssetService.update_asset() contains the 'hardware_serial_number' key
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause (e.g., "hardware_serial_number not in data dictionary", "serial number lost after update")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Hardware-Serial-Number Updates
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (desktop/server asset updates, other field updates)
  - Observe: Desktop asset update with manufacturer change works correctly on unfixed code
  - Observe: Server asset update with operating system change works correctly on unfixed code
  - Observe: Laptop asset creation with hardware serial number works correctly on unfixed code
  - Observe: Manual IP and OS entry handling works correctly on unfixed code
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For all desktop asset updates, all fields update correctly (no hardware serial number involved)
    - For all server asset updates, all fields update correctly (no hardware serial number involved)
    - For all asset updates with manual IP entry, manual IP handling works correctly
    - For all asset updates with manual OS entry, manual OS handling works correctly
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for laptop hardware serial number loss on edit

  - [x] 3.1 Implement the fix in AssetUpdateView.form_valid()
    - Add 'hardware_serial_number' field to the data dictionary in assets/views.py (around line 163)
    - Add: `'hardware_serial_number': form.cleaned_data.get('hardware_serial_number', ''),`
    - Ensure the field is included in the data dictionary passed to AssetService.update_asset()
    - _Bug_Condition: isBugCondition(input) where input.asset.system_type IN ['Laptop', 'All-in-One PC'] AND input.asset.hardware_serial_number IS NOT NULL_
    - _Expected_Behavior: Hardware serial number SHALL be included in data dictionary and preserved during update (from design)_
    - _Preservation: Desktop/server updates, other field updates, manual IP/OS handling must remain unchanged (from Preservation Requirements in design)_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.2 Implement the fix in AssetService.update_asset()
    - Add hardware_serial_number field handling in assets/services/asset_service.py (after line 118)
    - Add conditional block following existing pattern:
      ```python
      if 'hardware_serial_number' in data:
          asset.hardware_serial_number = data['hardware_serial_number']
      ```
    - Ensure the service method updates the hardware_serial_number field when present in data dictionary
    - _Bug_Condition: isBugCondition(input) where 'hardware_serial_number' NOT IN data_dictionary_passed_to_service_
    - _Expected_Behavior: Service method SHALL update hardware_serial_number field when present in data dictionary (from design)_
    - _Preservation: All other field update logic must remain unchanged (from Preservation Requirements in design)_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Hardware Serial Number Preserved on Laptop/All-in-One PC Edit
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Hardware-Serial-Number Updates
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
