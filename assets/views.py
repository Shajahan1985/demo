from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from .models import Asset
from .forms import AssetForm
from .forms.import_form import AssetImportForm
from .forms.filter_form import AssetFilterForm
from .permissions import AdminRequiredMixin
from .services.asset_service import AssetService
from .services.import_service import ImportService
from .services.export_service import ExportService
from .services.filter_service import FilterService


class AssetListView(LoginRequiredMixin, ListView):
    """Display all active assets ordered by serial number with filtering support."""
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    login_url = '/login/'

    def get_queryset(self):
        """Return active assets with filters applied, ordered by serial_number."""
        # Start with base queryset of active assets
        queryset = Asset.objects.filter(status='active').select_related(
            'operating_system', 'ip_address', 'team', 'team__parent'
        ).order_by('serial_number')
        
        # Initialize filter form with GET parameters
        filter_form = AssetFilterForm(self.request.GET)
        
        # Apply filters if form is valid
        if filter_form.is_valid():
            filter_service = FilterService()
            queryset = filter_service.apply_filters(queryset, filter_form.cleaned_data)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter form to template context."""
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form with GET parameters to preserve filter values
        context['filter_form'] = AssetFilterForm(self.request.GET)
        
        return context


class AssetCreateView(AdminRequiredMixin, CreateView):
    """Handle asset creation (admin only)."""
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset_list')

    def form_valid(self, form):
        """Process form submission using AssetService.create_asset()."""
        try:
            # Prepare data dictionary from cleaned form data
            data = {
                'asset_tag': form.cleaned_data['asset_tag'],
                'system_type': form.cleaned_data['system_type'],
                'hardware_serial_number': form.cleaned_data.get('hardware_serial_number', ''),
                'operating_system': form.cleaned_data['operating_system'].id,
                'ip_address': form.cleaned_data['ip_address'].id if form.cleaned_data.get('ip_address') else None,
                'particulars': form.cleaned_data.get('particulars', ''),
                'assigned_to': form.cleaned_data.get('assigned_to', ''),
                'team': form.cleaned_data['team'].id if form.cleaned_data.get('team') else None,
                'warranty_expiration': form.cleaned_data.get('warranty_expiration'),
            }

            # Create asset using service
            asset = AssetService.create_asset(data, self.request.user)

            # Display success message
            messages.success(self.request, f'Asset {asset.asset_tag} created successfully.')

            return redirect(self.success_url)

        except ValidationError as e:
            # Handle validation errors
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))

            return self.form_invalid(form)
        except Exception as e:
            # Handle unexpected errors
            messages.error(self.request, f'Error creating asset: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class AssetUpdateView(AdminRequiredMixin, CreateView):
    """Handle asset updates (admin only)."""
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset_list')
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        """Get the asset to update."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Asset, pk=self.kwargs.get(self.pk_url_kwarg))

    def get_form_kwargs(self):
        """Pass the asset instance to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        """Process form submission using AssetService.update_asset()."""
        try:
            asset = self.get_object()
            
            # Prepare data dictionary from cleaned form data
            data = {
                'asset_tag': form.cleaned_data['asset_tag'],
                'system_type': form.cleaned_data['system_type'],
                'operating_system': form.cleaned_data['operating_system'].id,
                'ip_address': form.cleaned_data['ip_address'].id if form.cleaned_data.get('ip_address') else None,
                'particulars': form.cleaned_data.get('particulars', ''),
                'assigned_to': form.cleaned_data.get('assigned_to', ''),
                'team': form.cleaned_data['team'].id if form.cleaned_data.get('team') else None,
                'warranty_expiration': form.cleaned_data.get('warranty_expiration'),
            }

            # Update asset using service
            updated_asset = AssetService.update_asset(asset, data, self.request.user)

            # Display success message
            messages.success(self.request, f'Asset {updated_asset.asset_tag} updated successfully.')

            return redirect(self.success_url)

        except ValidationError as e:
            # Handle validation errors
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))

            return self.form_invalid(form)
        except Exception as e:
            # Handle unexpected errors
            messages.error(self.request, f'Error updating asset: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class FreeSystemsView(LoginRequiredMixin, ListView):
    """Display all freed assets."""
    model = Asset
    template_name = 'assets/freed_systems.html'
    context_object_name = 'freed_assets'
    login_url = '/login/'

    def get_queryset(self):
        """Return only freed assets."""
        return Asset.objects.filter(status='freed').select_related(
            'ip_address'
        ).order_by('-freed_date')


class ScrappedItemsView(LoginRequiredMixin, ListView):
    """Display all scrapped assets ordered by scrapped_date descending."""
    model = Asset
    template_name = 'assets/scrapped_items.html'
    context_object_name = 'scrapped_assets'
    login_url = '/login/'

    def get_queryset(self):
        """Return only scrapped assets ordered by scrapped_date descending."""
        return Asset.objects.filter(status='scrapped').select_related(
            'ip_address'
        ).order_by('-scrapped_date')


class FreeIPsView(LoginRequiredMixin, ListView):
    """Display free IP addresses grouped by range."""
    model = Asset
    template_name = 'assets/free_ips.html'
    context_object_name = 'ip_ranges'
    login_url = '/login/'

    def get_queryset(self):
        """Return free IPs grouped by range using IPManagementService."""
        from .services.ip_management_service import IPManagementService
        return IPManagementService.get_free_ips_by_range()

    def get_context_data(self, **kwargs):
        """Add grouped IPs dict to template context."""
        context = super().get_context_data(**kwargs)
        # The queryset is already the grouped dict from get_free_ips_by_range()
        context['ip_ranges'] = self.get_queryset()
        return context


class AssetFreeView(AdminRequiredMixin, CreateView):
    """Handle freeing assets (admin only)."""
    model = Asset
    template_name = 'assets/asset_free_confirm.html'
    success_url = reverse_lazy('freed_systems')
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        """Get the asset to free."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Asset, pk=self.kwargs.get(self.pk_url_kwarg))

    def get_context_data(self, **kwargs):
        """Add asset to context for display in confirmation dialog."""
        context = super().get_context_data(**kwargs)
        context['asset'] = self.get_object()
        return context

    def get(self, request, *args, **kwargs):
        """Display confirmation dialog and password prompt."""
        from .forms.asset_forms import FreeAssetForm
        asset = self.get_object()
        form = FreeAssetForm()
        return render(request, self.template_name, {
            'asset': asset,
            'form': form
        })

    def post(self, request, *args, **kwargs):
        """Process POST with password verification."""
        from .forms.asset_forms import FreeAssetForm
        
        asset = self.get_object()
        form = FreeAssetForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']
            
            try:
                # Call AssetService.free_asset() with password
                freed_asset = AssetService.free_asset(asset, request.user, password)
                
                # Display success message
                messages.success(request, f'Asset {freed_asset.asset_tag} has been freed successfully.')
                
                # Redirect to freed systems page on success
                return redirect(self.success_url)
                
            except ValidationError as e:
                # Handle incorrect password errors
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            if field == 'password':
                                messages.error(request, error)
                            form.add_error(field, error)
                else:
                    messages.error(request, str(e))
                    form.add_error(None, str(e))
            except Exception as e:
                # Handle unexpected errors
                messages.error(request, f'Error freeing asset: {str(e)}')
                form.add_error(None, str(e))
        else:
            messages.error(request, 'Please correct the errors below.')

        # Re-render form with errors
        return render(request, self.template_name, {
            'asset': asset,
            'form': form
        })


class AssetScrapView(AdminRequiredMixin, CreateView):
    """Handle scrapping freed assets (admin only)."""
    model = Asset
    template_name = 'assets/asset_scrap_confirm.html'
    success_url = reverse_lazy('scrapped_items')
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        """Get the asset to scrap."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Asset, pk=self.kwargs.get(self.pk_url_kwarg))

    def get_context_data(self, **kwargs):
        """Add asset to context for display in confirmation dialog."""
        context = super().get_context_data(**kwargs)
        context['asset'] = self.get_object()
        return context

    def get(self, request, *args, **kwargs):
        """Display confirmation dialog."""
        asset = self.get_object()
        return render(request, self.template_name, {
            'asset': asset
        })

    def post(self, request, *args, **kwargs):
        """Process POST to scrap the asset."""
        asset = self.get_object()

        try:
            # Verify asset is freed before scrapping
            if asset.status != 'freed':
                messages.error(request, 'Only freed assets can be scrapped.')
                return redirect('freed_systems')

            # Call AssetService.scrap_asset()
            scrapped_asset = AssetService.scrap_asset(asset, request.user)

            # Display success message
            messages.success(request, f'Asset {scrapped_asset.asset_tag} has been scrapped successfully.')

            # Redirect to scrapped items page on success
            return redirect(self.success_url)

        except ValidationError as e:
            # Handle validation errors
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, error)
            else:
                messages.error(request, str(e))
            return redirect('freed_systems')
        except Exception as e:
            # Handle unexpected errors
            messages.error(request, f'Error scrapping asset: {str(e)}')
            return redirect('freed_systems')


class WarrantyView(LoginRequiredMixin, ListView):
    """Display all assets with warranty information."""
    model = Asset
    template_name = 'assets/warranty.html'
    context_object_name = 'assets'
    login_url = '/login/'

    def get_queryset(self):
        """Return all assets with warranty dates ordered by warranty_expiration ascending."""
        return Asset.objects.filter(
            warranty_expiration__isnull=False
        ).select_related(
            'operating_system', 'ip_address', 'team', 'team__parent'
        ).order_by('warranty_expiration')

    def get_context_data(self, **kwargs):
        """Add expiring_soon assets to context using WarrantyService."""
        from .services.warranty_service import WarrantyService
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        # Get assets expiring within 7 days for highlighting
        context['expiring_soon'] = WarrantyService.check_expiring_warranties()
        
        # Add today's date for expired check
        context['today'] = timezone.now().date()
        
        return context


class AssetImportView(AdminRequiredMixin, View):
    """Handle Excel file import for bulk asset creation (admin only)."""
    template_name = 'assets/asset_import.html'
    results_template_name = 'assets/asset_import_results.html'
    
    def get(self, request):
        """Display the import form or download template."""
        # Check if template download is requested
        if request.GET.get('download_template'):
            from django.http import FileResponse
            import os
            from django.conf import settings
            
            # Path to the sample template
            template_path = os.path.join(settings.MEDIA_ROOT, 'templates', 'sample_import_template.xlsx')
            
            # Check if file exists
            if os.path.exists(template_path):
                response = FileResponse(
                    open(template_path, 'rb'),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="sample_import_template.xlsx"'
                return response
            else:
                messages.error(request, "Sample template file not found.")
        
        # Display the import form
        form = AssetImportForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Process the uploaded Excel file and import assets."""
        form = AssetImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Get the uploaded file
            file = request.FILES['file']
            
            # Initialize ImportService and process the file
            import_service = ImportService()
            result = import_service.import_assets(file, request.user)
            
            # Display success message if any assets were imported
            if result['success_count'] > 0:
                messages.success(
                    request,
                    f"Successfully imported {result['success_count']} asset(s)."
                )
            
            # Display warning message if there were errors
            if result['error_count'] > 0:
                messages.warning(
                    request,
                    f"{result['error_count']} row(s) had errors and were not imported."
                )
            
            # Store results in session for the results page
            request.session['import_results'] = {
                'success_count': result['success_count'],
                'error_count': result['error_count'],
                'errors': result['errors']
            }
            
            # Redirect to the results page
            return redirect('asset_import_results')
        
        # Form validation failed, re-display form with errors
        return render(request, self.template_name, {'form': form})


class AssetImportResultsView(AdminRequiredMixin, View):
    """Display import results from session."""
    template_name = 'assets/asset_import_results.html'
    
    def get(self, request):
        """Display the import results stored in session."""
        # Retrieve results from session
        import_results = request.session.get('import_results', None)
        
        # If no results in session, redirect to import page
        if import_results is None:
            messages.info(request, "No import results to display.")
            return redirect('asset_import')
        
        # Clear the results from session after retrieving
        del request.session['import_results']
        
        return render(request, self.template_name, {
            'success_count': import_results['success_count'],
            'error_count': import_results['error_count'],
            'errors': import_results['errors']
        })


class AssetExportActiveView(LoginRequiredMixin, View):
    """Export active assets to Excel file."""
    login_url = '/login/'
    
    def get(self, request):
        """Generate and return Excel file with active assets."""
        export_service = ExportService()
        return export_service.export_active_assets()


class AssetExportFreedView(LoginRequiredMixin, View):
    """Export freed assets to Excel file."""
    login_url = '/login/'
    
    def get(self, request):
        """Generate and return Excel file with freed assets."""
        export_service = ExportService()
        return export_service.export_freed_assets()


class AssetExportScrappedView(LoginRequiredMixin, View):
    """Export scrapped assets to Excel file."""
    login_url = '/login/'
    
    def get(self, request):
        """Generate and return Excel file with scrapped assets."""
        export_service = ExportService()
        return export_service.export_scrapped_assets()


class FreeIPsExportView(LoginRequiredMixin, View):
    """Export free IP addresses to Excel file."""
    login_url = '/login/'
    
    def get(self, request):
        """Generate and return Excel file with free IP addresses."""
        export_service = ExportService()
        return export_service.export_free_ips()





class GetSubTeamsView(LoginRequiredMixin, View):
    """API endpoint to get sub-teams for a parent team."""
    login_url = '/login/'
    
    def get(self, request):
        """Return sub-teams as JSON for the given parent team ID."""
        from django.http import JsonResponse
        
        parent_id = request.GET.get('parent_id')
        
        if not parent_id:
            return JsonResponse({'sub_teams': []})
        
        try:
            parent_team = Team.objects.get(pk=parent_id)
            sub_teams = parent_team.sub_teams.all().order_by('name')
            
            sub_teams_data = [
                {'id': sub.id, 'name': sub.name}
                for sub in sub_teams
            ]
            
            return JsonResponse({
                'sub_teams': sub_teams_data,
                'has_sub_teams': len(sub_teams_data) > 0
            })
        except Team.DoesNotExist:
            return JsonResponse({'sub_teams': [], 'has_sub_teams': False})
