/**
 * Asset Tracker - Main JavaScript
 * Handles confirmation dialogs, form interactions, and UI enhancements
 */

(function() {
    'use strict';

    // ===== Confirmation Dialogs =====
    
    /**
     * Initialize confirmation dialogs for delete/scrap actions
     */
    function initConfirmationDialogs() {
        // Attachment deletion confirmation
        const attachmentDeleteForms = document.querySelectorAll('form[action*="delete_attachment"]');
        attachmentDeleteForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!confirm('Are you sure you want to delete this attachment?')) {
                    e.preventDefault();
                }
            });
        });

        // Asset scrap confirmation (additional confirmation beyond the page)
        const scrapForms = document.querySelectorAll('form[action*="scrap"]');
        scrapForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const assetTag = form.dataset.assetTag || 'this asset';
                if (!confirm(`Are you sure you want to scrap ${assetTag}? This action will move it to the Scrapped Items page.`)) {
                    e.preventDefault();
                }
            });
        });
    }

    // ===== Form Validation =====
    
    /**
     * Add real-time validation feedback to forms
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('form[novalidate]');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('.form-control');
            
            inputs.forEach(input => {
                // Add validation on blur
                input.addEventListener('blur', function() {
                    validateField(this);
                });
                
                // Remove error styling on input
                input.addEventListener('input', function() {
                    if (this.classList.contains('error')) {
                        this.classList.remove('error');
                    }
                });
            });
            
            // Validate on submit
            form.addEventListener('submit', function(e) {
                let isValid = true;
                
                inputs.forEach(input => {
                    if (!validateField(input)) {
                        isValid = false;
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    // Scroll to first error
                    const firstError = form.querySelector('.form-control.error');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstError.focus();
                    }
                }
            });
        });
    }
    
    /**
     * Validate a single form field
     */
    function validateField(field) {
        const isRequired = field.hasAttribute('required') || 
                          field.labels && Array.from(field.labels).some(label => label.classList.contains('required'));
        
        if (isRequired && !field.value.trim()) {
            field.classList.add('error');
            return false;
        }
        
        field.classList.remove('error');
        return true;
    }

    // ===== File Upload Enhancement =====
    
    /**
     * Show file name when file is selected
     */
    function initFileUpload() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', function() {
                const fileName = this.files[0]?.name;
                
                // Remove existing file name display
                const existingDisplay = this.parentElement.querySelector('.file-name-display');
                if (existingDisplay) {
                    existingDisplay.remove();
                }
                
                if (fileName) {
                    // Create file name display
                    const display = document.createElement('div');
                    display.className = 'file-name-display';
                    display.style.cssText = 'margin-top: 0.5rem; color: #27ae60; font-size: 0.875rem;';
                    display.innerHTML = `<strong>Selected:</strong> ${fileName}`;
                    this.parentElement.appendChild(display);
                }
            });
        });
    }

    // ===== Table Enhancements =====
    
    /**
     * Add sorting capability to tables
     */
    function initTableSorting() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            
            headers.forEach((header, index) => {
                // Skip action columns
                if (header.textContent.toLowerCase().includes('action')) {
                    return;
                }
                
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.title = 'Click to sort';
                
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
            });
        });
    }
    
    /**
     * Sort table by column index
     */
    function sortTable(table, columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Determine sort direction
        const currentDirection = table.dataset.sortDirection || 'asc';
        const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
        table.dataset.sortDirection = newDirection;
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex]?.textContent.trim() || '';
            const bValue = b.cells[columnIndex]?.textContent.trim() || '';
            
            // Try numeric comparison first
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // Fall back to string comparison
            return newDirection === 'asc' 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        });
        
        // Re-append rows in sorted order
        rows.forEach(row => tbody.appendChild(row));
        
        // Update header indicators
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            // Remove existing indicators
            header.textContent = header.textContent.replace(/\s*[▲▼]$/, '');
            
            // Add indicator to sorted column
            if (index === columnIndex) {
                header.textContent += newDirection === 'asc' ? ' ▲' : ' ▼';
            }
        });
    }

    // ===== Search/Filter Enhancement =====
    
    /**
     * Add quick search functionality to tables
     */
    function initTableSearch() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            // Create search input
            const searchContainer = document.createElement('div');
            searchContainer.className = 'table-search';
            searchContainer.style.cssText = 'margin-bottom: 1rem;';
            
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.className = 'form-control';
            searchInput.placeholder = 'Search table...';
            searchInput.style.maxWidth = '300px';
            
            searchContainer.appendChild(searchInput);
            table.parentElement.insertBefore(searchContainer, table);
            
            // Add search functionality
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const tbody = table.querySelector('tbody');
                const rows = tbody.querySelectorAll('tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        });
    }

    // ===== Loading State for Forms =====
    
    /**
     * Show loading state when form is submitted
     */
    function initFormLoadingState() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitButton = this.querySelector('button[type="submit"]');
                
                if (submitButton && !submitButton.disabled) {
                    submitButton.disabled = true;
                    const originalText = submitButton.textContent;
                    submitButton.innerHTML = '<span class="spinner"></span> Processing...';
                    
                    // Re-enable after 5 seconds as fallback
                    setTimeout(() => {
                        submitButton.disabled = false;
                        submitButton.textContent = originalText;
                    }, 5000);
                }
            });
        });
    }

    // ===== Auto-dismiss Alerts =====
    
    /**
     * Auto-dismiss success alerts after 5 seconds
     */
    function initAutoDismissAlerts() {
        const successAlerts = document.querySelectorAll('.alert-success');
        
        successAlerts.forEach(alert => {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        });
    }

    // ===== Warranty Expiration Highlighting =====
    
    /**
     * Add visual indicators for warranty status
     */
    function initWarrantyHighlighting() {
        const warrantyRows = document.querySelectorAll('.warranty-expiring-soon, .warranty-expired');
        
        warrantyRows.forEach(row => {
            // Add a subtle animation on page load
            row.style.animation = 'fadeIn 0.5s ease-in';
        });
    }

    // ===== Keyboard Shortcuts =====
    
    /**
     * Add keyboard shortcuts for common actions
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Alt+N: New Asset (if on asset list page and user is admin)
            if (e.altKey && e.key === 'n') {
                const newAssetLink = document.querySelector('a[href*="create"]');
                if (newAssetLink) {
                    e.preventDefault();
                    newAssetLink.click();
                }
            }
            
            // Escape: Cancel/Go back
            if (e.key === 'Escape') {
                const cancelButton = document.querySelector('.btn-secondary');
                if (cancelButton && cancelButton.textContent.includes('Cancel')) {
                    cancelButton.click();
                }
            }
        });
    }

    // ===== Responsive Table Enhancement =====
    
    /**
     * Make tables more mobile-friendly by adding data labels
     */
    function initResponsiveTables() {
        if (window.innerWidth <= 768) {
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    cells.forEach((cell, index) => {
                        if (headers[index]) {
                            cell.setAttribute('data-label', headers[index]);
                        }
                    });
                });
            });
        }
    }

    // ===== Initialize All Features =====
    
    /**
     * Initialize all JavaScript features when DOM is ready
     */
    function init() {
        initConfirmationDialogs();
        initFormValidation();
        initFileUpload();
        initTableSorting();
        initFormLoadingState();
        initAutoDismissAlerts();
        initWarrantyHighlighting();
        initKeyboardShortcuts();
        initResponsiveTables();
        
        // Optional: Uncomment to enable table search
        // initTableSearch();
    }

    // Run initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Add CSS animation for warranty highlighting
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);

})();
