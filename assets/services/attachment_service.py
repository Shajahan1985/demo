"""
Attachment service for managing file attachments.
"""
import os
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from assets.models import Attachment


class AttachmentService:
    """Service class for attachment management."""
    
    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    # Allowed file types
    ALLOWED_EXTENSIONS = {
        'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip'
    }
    
    @staticmethod
    def upload_attachment(asset, file):
        """
        Upload a file attachment for an asset.
        
        Args:
            asset: Asset instance to attach the file to
            file: UploadedFile instance from Django form
            
        Returns:
            Attachment: Created Attachment instance
            
        Raises:
            ValidationError: If file size exceeds limit or file type not allowed
        """
        # Validate file size
        if file.size > AttachmentService.MAX_FILE_SIZE:
            raise ValidationError({
                'file': f'File size exceeds the maximum limit of {AttachmentService.MAX_FILE_SIZE / (1024 * 1024):.0f}MB'
            })
        
        # Validate file type
        file_extension = os.path.splitext(file.name)[1][1:].lower()  # Get extension without dot
        if file_extension not in AttachmentService.ALLOWED_EXTENSIONS:
            raise ValidationError({
                'file': f'File type .{file_extension} is not allowed. Allowed types: {", ".join(sorted(AttachmentService.ALLOWED_EXTENSIONS))}'
            })
        
        # Create attachment record
        attachment = Attachment.objects.create(
            asset=asset,
            file=file,
            filename=file.name
        )
        
        return attachment
    
    @staticmethod
    def delete_attachment(attachment):
        """
        Delete an attachment and remove its file from storage.
        
        Args:
            attachment: Attachment instance to delete
        """
        # Delete the file from storage
        if attachment.file:
            # Use default_storage to ensure compatibility with different storage backends
            if default_storage.exists(attachment.file.name):
                default_storage.delete(attachment.file.name)
        
        # Delete the attachment record
        attachment.delete()
    
    @staticmethod
    def get_asset_attachments(asset):
        """
        Get all attachments for an asset.
        
        Args:
            asset: Asset instance
            
        Returns:
            QuerySet: Queryset of Attachment instances ordered by upload date (newest first)
        """
        return asset.attachments.all()
