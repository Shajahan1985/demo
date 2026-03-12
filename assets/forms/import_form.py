"""
Import form for Excel file upload.

This form handles file upload validation for bulk asset imports,
including file format and size validation.
"""

from django import forms


class AssetImportForm(forms.Form):
    """Form for uploading Excel files to import assets."""
    
    file = forms.FileField(
        label='Excel File',
        help_text='Upload .xlsx or .xls file (max 10MB)',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )
    
    def clean_file(self):
        """
        Validate uploaded file format and size.
        
        Returns:
            Cleaned file object
            
        Raises:
            ValidationError: If file format or size is invalid
        """
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError('No file uploaded')
        
        # Validate file extension
        valid_extensions = ['.xlsx', '.xls']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise forms.ValidationError(
                'Invalid file format. Please upload .xlsx or .xls file'
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file.size > max_size:
            raise forms.ValidationError(
                'File too large. Maximum size is 10MB'
            )
        
        return file
