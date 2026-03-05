# Assets App Structure

This Django app manages the Asset Tracking System.

## Directory Structure

```
assets/
├── forms/                  # Django forms for asset management
│   ├── __init__.py
│   └── asset_forms.py     # AssetForm, FreeAssetForm, AttachmentForm
├── migrations/            # Database migrations
├── permissions/           # Permission decorators and mixins
│   ├── __init__.py
│   └── decorators.py     # AdminRequiredMixin, admin_required
├── services/             # Business logic services
│   ├── __init__.py
│   ├── asset_service.py
│   ├── attachment_service.py
│   ├── ip_management_service.py
│   └── warranty_service.py
├── static/               # Static files (CSS, JS)
│   └── assets/
│       ├── css/
│       └── js/
├── templates/            # HTML templates
│   └── assets/
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_views.py
│   └── test_properties.py
├── __init__.py
├── admin.py             # Django admin configuration
├── apps.py              # App configuration
├── models.py            # Data models
├── tasks.py             # Celery tasks
└── views.py             # View functions and classes
```

## Testing

Run tests with pytest:
```bash
pytest
```

Run property-based tests:
```bash
pytest -m property
```

## Development

The app follows Django's MVT architecture with additional service layers for business logic.
