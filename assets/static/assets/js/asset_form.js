/**
 * Asset Form - Hardware Serial Number Field Toggle
 */

console.log('[Asset Form] Script loaded');

// Hardware Serial Number Field Toggle
function handleSystemTypeChange(systemType) {
    console.log('[Hardware Serial] handleSystemTypeChange called with:', systemType);
    
    const hardwareSerialNumberGroup = document.getElementById('hardware_serial_number_group');
    const hardwareSerialNumberInput = document.getElementById('id_hardware_serial_number');
    const hardwareSerialNumberLabel = hardwareSerialNumberGroup ? hardwareSerialNumberGroup.querySelector('label') : null;
    
    console.log('[Hardware Serial] Group element:', hardwareSerialNumberGroup);
    console.log('[Hardware Serial] Input element:', hardwareSerialNumberInput);
    console.log('[Hardware Serial] Label element:', hardwareSerialNumberLabel);
    
    // Show/hide and make required for Laptop and All-in-One PC
    if (systemType === 'Laptop' || systemType === 'All-in-One PC') {
        console.log('[Hardware Serial] Showing field for:', systemType);
        if (hardwareSerialNumberGroup) {
            hardwareSerialNumberGroup.style.display = 'block';
            console.log('[Hardware Serial] Group display set to block');
        }
        if (hardwareSerialNumberInput) {
            hardwareSerialNumberInput.required = true;
            console.log('[Hardware Serial] Input required set to true');
        }
        if (hardwareSerialNumberLabel && !hardwareSerialNumberLabel.classList.contains('required')) {
            hardwareSerialNumberLabel.classList.add('required');
            console.log('[Hardware Serial] Added required class to label');
        }
    } else {
        console.log('[Hardware Serial] Hiding field for:', systemType);
        if (hardwareSerialNumberGroup) {
            hardwareSerialNumberGroup.style.display = 'none';
            console.log('[Hardware Serial] Group display set to none');
        }
        if (hardwareSerialNumberInput) {
            hardwareSerialNumberInput.required = false;
            hardwareSerialNumberInput.value = '';  // Clear the value when hidden
            console.log('[Hardware Serial] Input required set to false and value cleared');
        }
        if (hardwareSerialNumberLabel) {
            hardwareSerialNumberLabel.classList.remove('required');
            console.log('[Hardware Serial] Removed required class from label');
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Asset Form] DOM Content Loaded - Initializing form');
    
    // Initialize hardware serial number field visibility
    const systemTypeSelect = document.getElementById('id_system_type');
    console.log('[Asset Form] System type select element:', systemTypeSelect);
    
    if (systemTypeSelect) {
        console.log('[Asset Form] Initial system type value:', systemTypeSelect.value);
        
        // Initialize visibility based on current value
        if (systemTypeSelect.value) {
            handleSystemTypeChange(systemTypeSelect.value);
        }
        
        // Attach the change event listener
        systemTypeSelect.addEventListener('change', function() {
            console.log('[Asset Form] Change event fired, new value:', this.value);
            handleSystemTypeChange(this.value);
        });
        
        console.log('[Asset Form] Event listener attached successfully');
    } else {
        console.error('[Asset Form] ERROR: System type select element not found!');
    }
    
    console.log('[Asset Form] Initialization complete');
});
