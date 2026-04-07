from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from .models import Asset, OperatingSystem, Team
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
            # Check if manual OS entry was provided
            os_manual_entry = self.request.POST.get('os_manual_entry', '').strip()
            
            if os_manual_entry:
                os_obj, created = OperatingSystem.objects.get_or_create(name=os_manual_entry)
                operating_system_id = os_obj.id
            else:
                operating_system_id = form.cleaned_data['operating_system'].id
            
            # Check if manual IP entry was provided
            ip_manual_entry = self.request.POST.get('ip_manual_entry', '').strip()
            
            # Prepare data dictionary from cleaned form data
            data = {
                'asset_tag': form.cleaned_data['asset_tag'],
                'system_type': form.cleaned_data['system_type'],
                'hardware_serial_number': form.cleaned_data.get('hardware_serial_number', ''),
                'manufacturer': form.cleaned_data.get('manufacturer', ''),
                'operating_system': operating_system_id,
                'ip_address': form.cleaned_data['ip_address'].id if form.cleaned_data.get('ip_address') else None,
                'manual_ip': ip_manual_entry if ip_manual_entry else None,
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
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))

            return self.form_invalid(form)
        except Exception as e:
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
            
            # Check if manual OS entry was provided
            os_manual_entry = self.request.POST.get('os_manual_entry', '').strip()
            
            if os_manual_entry:
                os_obj, created = OperatingSystem.objects.get_or_create(name=os_manual_entry)
                operating_system_id = os_obj.id
            else:
                operating_system_id = form.cleaned_data['operating_system'].id
            
            # Check if manual IP entry was provided
            ip_manual_entry = self.request.POST.get('ip_manual_entry', '').strip()
            
            # Prepare data dictionary from cleaned form data
            data = {
                'asset_tag': form.cleaned_data['asset_tag'],
                'system_type': form.cleaned_data['system_type'],
                'manufacturer': form.cleaned_data.get('manufacturer', ''),
                'operating_system': operating_system_id,
                'ip_address': form.cleaned_data['ip_address'].id if form.cleaned_data.get('ip_address') else None,
                'manual_ip': ip_manual_entry if ip_manual_entry else None,
                'particulars': form.cleaned_data.get('particulars', ''),
                'assigned_to': form.cleaned_data.get('assigned_to', ''),
                'team': form.cleaned_data['team'].id if form.cleaned_data.get('team') else None,
                'warranty_expiration': form.cleaned_data.get('warranty_expiration'),
                'hardware_serial_number': form.cleaned_data.get('hardware_serial_number', ''),
            }

            # Update asset using service
            updated_asset = AssetService.update_asset(asset, data, self.request.user)

            messages.success(self.request, f'Asset {updated_asset.asset_tag} updated successfully.')
            return redirect(self.success_url)

        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
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
            'operating_system', 'ip_address'
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
    """Display all IP addresses grouped by range with free/occupied status."""
    model = Asset
    template_name = 'assets/free_ips.html'
    context_object_name = 'ip_ranges'
    login_url = '/login/'

    def get_queryset(self):
        """Return all IPs grouped by range using IPManagementService."""
        from .services.ip_management_service import IPManagementService
        return IPManagementService.get_all_ips_by_range()

    def get_context_data(self, **kwargs):
        """Add grouped IPs dict to template context with network device information."""
        from .services.ip_management_service import IPManagementService
        
        context = super().get_context_data(**kwargs)
        
        # Get IP ranges with occupant information
        ip_ranges = self.get_queryset()
        
        # Enhance each IP with occupant info
        for range_pattern, ips in ip_ranges.items():
            for ip in ips:
                occupant_info = IPManagementService.get_ip_occupant_info(ip)
                ip.occupant_type = occupant_info['type']
                ip.occupant_name = occupant_info['name']
        
        context['ip_ranges'] = ip_ranges
        
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
        from django.urls import reverse
        
        asset = self.get_object()
        form = FreeAssetForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']
            
            try:
                # Call AssetService.free_asset() with password
                freed_asset = AssetService.free_asset(asset, request.user, password)
                
                # Display success message
                messages.success(request, f'Asset {freed_asset.asset_tag} has been freed successfully.')
                
                # Redirect to freed systems page on success using reverse() for absolute path
                return redirect(reverse('freed_systems'))
                
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
            # Get scrapping_reason from POST data
            scrapping_reason = request.POST.get('scrapping_reason', '').strip()
            
            # Verify asset is freed before scrapping
            if asset.status != 'freed':
                messages.error(request, 'Only freed assets can be scrapped.')
                return redirect('freed_systems')

            # Call AssetService.scrap_asset() with scrapping_reason
            scrapped_asset = AssetService.scrap_asset(asset, request.user, scrapping_reason)

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
            
            # Display success message if any assets were created or updated
            if result['created_count'] > 0 or result['updated_count'] > 0:
                messages.success(
                    request,
                    f"{result['created_count']} asset(s) created, {result['updated_count']} asset(s) updated."
                )
            
            # Display warning message if there were errors
            if result['error_count'] > 0:
                messages.warning(
                    request,
                    f"{result['error_count']} row(s) had errors and were not imported."
                )
            
            # Store results in session for the results page
            request.session['import_results'] = {
                'created_count': result['created_count'],
                'updated_count': result['updated_count'],
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
            'created_count': import_results['created_count'],
            'updated_count': import_results['updated_count'],
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



class OperatingSystemListView(AdminRequiredMixin, ListView):
    """Display all operating systems with management options."""
    model = OperatingSystem
    template_name = 'assets/operating_systems.html'
    context_object_name = 'operating_systems'
    login_url = '/login/'
    
    def get_queryset(self):
        """Return all operating systems ordered by name."""
        from .models import OperatingSystem
        return OperatingSystem.objects.all().order_by('name')


class AddOperatingSystemView(AdminRequiredMixin, View):
    """Add a new operating system."""
    login_url = '/login/'
    
    def post(self, request):
        """Handle POST request to add new OS."""
        from .models import OperatingSystem
        
        os_name = request.POST.get('os_name', '').strip()
        
        if not os_name:
            messages.error(request, 'Operating system name is required.')
            return redirect('operating_systems')
        
        # Check if OS already exists
        if OperatingSystem.objects.filter(name=os_name).exists():
            messages.error(request, f'Operating system "{os_name}" already exists.')
            return redirect('operating_systems')
        
        # Create new OS
        OperatingSystem.objects.create(name=os_name)
        messages.success(request, f'Operating system "{os_name}" added successfully.')
        
        return redirect('operating_systems')


class EditOperatingSystemView(AdminRequiredMixin, View):
    """Edit an existing operating system."""
    login_url = '/login/'
    
    def post(self, request, pk):
        """Handle POST request to edit OS."""
        from .models import OperatingSystem
        from django.shortcuts import get_object_or_404
        
        os_obj = get_object_or_404(OperatingSystem, pk=pk)
        os_name = request.POST.get('os_name', '').strip()
        
        if not os_name:
            messages.error(request, 'Operating system name is required.')
            return redirect('operating_systems')
        
        # Check if new name already exists (excluding current OS)
        if OperatingSystem.objects.filter(name=os_name).exclude(pk=pk).exists():
            messages.error(request, f'Operating system "{os_name}" already exists.')
            return redirect('operating_systems')
        
        # Update OS name
        old_name = os_obj.name
        os_obj.name = os_name
        os_obj.save()
        
        messages.success(request, f'Operating system updated from "{old_name}" to "{os_name}".')
        
        return redirect('operating_systems')


class DeleteOperatingSystemView(AdminRequiredMixin, View):
    """Delete an operating system."""
    login_url = '/login/'
    
    def post(self, request, pk):
        """Handle POST request to delete OS."""
        from .models import OperatingSystem
        from django.shortcuts import get_object_or_404
        
        os_obj = get_object_or_404(OperatingSystem, pk=pk)
        
        # Check if OS is in use
        if os_obj.assets.exists():
            messages.error(request, f'Cannot delete "{os_obj.name}" - it is in use by {os_obj.assets.count()} asset(s).')
            return redirect('operating_systems')
        
        # Delete OS
        os_name = os_obj.name
        os_obj.delete()
        
        messages.success(request, f'Operating system "{os_name}" deleted successfully.')
        
        return redirect('operating_systems')



class FreedSystemCreateView(AdminRequiredMixin, CreateView):
    """Handle manual freed system creation (admin only)."""
    model = Asset
    template_name = 'assets/freed_system_create.html'
    success_url = reverse_lazy('freed_systems')
    
    def get_form_class(self):
        from .forms.freed_system_forms import FreedSystemForm
        return FreedSystemForm
    
    def form_valid(self, form):
        """Process form submission using AssetService.create_freed_asset()."""
        try:
            asset = AssetService.create_freed_asset(
                form.cleaned_data,
                self.request.user
            )
            messages.success(
                self.request,
                f'Freed system {asset.asset_tag} created successfully.'
            )
            return redirect(self.success_url)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating freed system: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class FreedSystemEditView(AdminRequiredMixin, CreateView):
    """Handle freed system health status updates (admin only)."""
    model = Asset
    template_name = 'assets/freed_system_edit.html'
    success_url = reverse_lazy('freed_systems')
    pk_url_kwarg = 'pk'
    
    def get_form_class(self):
        from .forms.freed_system_forms import FreedSystemEditForm
        return FreedSystemEditForm
    
    def get_object(self, queryset=None):
        """Get the freed asset to edit."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Asset, pk=self.kwargs.get(self.pk_url_kwarg), status='freed')
    
    def get_form_kwargs(self):
        """Pass the asset instance to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add asset to context."""
        context = super().get_context_data(**kwargs)
        context['asset'] = self.get_object()
        return context
    
    def form_valid(self, form):
        """Process form submission using AssetService.update_freed_asset()."""
        try:
            asset = self.get_object()
            updated_asset = AssetService.update_freed_asset(
                asset,
                form.cleaned_data,
                self.request.user
            )
            messages.success(
                self.request,
                f'Freed system {updated_asset.asset_tag} updated successfully.'
            )
            return redirect(self.success_url)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error updating freed system: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class AssetReassignView(AdminRequiredMixin, View):
    """Handle reassignment of freed assets back to active status (admin only)."""
    template_name = 'assets/asset_reassign_form.html'
    success_url = reverse_lazy('asset_list')
    
    def get(self, request, pk):
        """Display reassignment form for freed asset."""
        from django.shortcuts import get_object_or_404
        from .forms.asset_forms import ReassignmentForm
        
        # Get the asset
        asset = get_object_or_404(Asset, pk=pk)
        
        # Verify asset is freed
        if asset.status != 'freed':
            messages.error(request, 'Only freed assets can be reassigned.')
            return redirect('freed_systems')
        
        # Verify asset is healthy
        if asset.health_status != 'healthy':
            messages.error(request, 'Only healthy freed assets can be reassigned.')
            return redirect('freed_systems')
        
        # Create form with asset data
        form = ReassignmentForm(asset=asset)
        
        return render(request, self.template_name, {
            'asset': asset,
            'form': form
        })
    
    def post(self, request, pk):
        """Process reassignment submission."""
        from django.shortcuts import get_object_or_404
        from .forms.asset_forms import ReassignmentForm
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"=== REASSIGNMENT POST REQUEST ===")
        logger.info(f"Asset PK: {pk}")
        logger.info(f"POST data: {request.POST}")
        
        # Get the asset
        asset = get_object_or_404(Asset, pk=pk)
        logger.info(f"Asset: {asset.asset_tag}, Status: {asset.status}, Health: {asset.health_status}")
        
        # Verify asset is freed
        if asset.status != 'freed':
            messages.error(request, 'Only freed assets can be reassigned.')
            logger.error(f"Asset {asset.asset_tag} is not freed (status={asset.status})")
            return redirect('freed_systems')
        
        # Verify asset is healthy
        if asset.health_status != 'healthy':
            messages.error(request, 'Only healthy freed assets can be reassigned.')
            logger.error(f"Asset {asset.asset_tag} is not healthy (health={asset.health_status})")
            return redirect('freed_systems')
        
        # Create form with POST data
        form = ReassignmentForm(request.POST, asset=asset)
        logger.info(f"Form is_valid: {form.is_valid()}")
        
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
            return render(request, self.template_name, {
                'asset': asset,
                'form': form
            })
        
        try:
            # Check if manual OS entry was provided
            os_manual_entry = request.POST.get('os_manual_entry', '').strip()
            logger.info(f"OS manual entry: '{os_manual_entry}'")
            
            if os_manual_entry:
                os_obj, created = OperatingSystem.objects.get_or_create(name=os_manual_entry)
                operating_system_id = os_obj.id
                logger.info(f"Created/found OS: {os_obj.name} (id={os_obj.id})")
            else:
                operating_system_id = form.cleaned_data['operating_system'].id if form.cleaned_data.get('operating_system') else None
                logger.info(f"Using OS from dropdown: {operating_system_id}")
            
            # Prepare data dictionary (only manual_ip now, no dropdown)
            data = {
                'assigned_to': form.cleaned_data['assigned_to'],
                'team': form.cleaned_data['team'].id,
                'ip_address_id': None,  # No longer using dropdown
                'manual_ip': form.cleaned_data.get('manual_ip'),
                'operating_system': operating_system_id,
                'system_type': form.cleaned_data['system_type'],
                'manufacturer': form.cleaned_data.get('manufacturer', ''),
                'particulars': form.cleaned_data.get('particulars', ''),
                'warranty_expiration': form.cleaned_data.get('warranty_expiration'),
            }
            logger.info(f"Reassignment data: {data}")
            
            # Call service method
            reassigned_asset = AssetService.reassign_asset(asset, data, request.user)
            logger.info(f"Asset reassigned successfully: {reassigned_asset.asset_tag}")
            
            # Display success message
            messages.success(request, f'Asset {reassigned_asset.asset_tag} has been reassigned and is now active.')
            
            # Redirect to active assets page
            return redirect(self.success_url)
            
        except ValidationError as e:
            # Handle validation errors
            logger.error(f"ValidationError: {e}")
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                        logger.error(f"Field error - {field}: {error}")
            else:
                form.add_error(None, str(e))
                logger.error(f"General error: {str(e)}")
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error: {str(e)}")
            messages.error(request, f'Error reassigning asset: {str(e)}')
            form.add_error(None, str(e))
        
        # Re-render form with errors
        return render(request, self.template_name, {
            'asset': asset,
            'form': form
        })



class NetworkDeviceListView(AdminRequiredMixin, ListView):
    """Display all network devices."""
    template_name = 'assets/network_device_list.html'
    context_object_name = 'devices'
    login_url = '/login/'
    
    def get_queryset(self):
        from assets.models import NetworkDevice
        return NetworkDevice.objects.select_related('ip_address').order_by('device_name')


class NetworkDeviceCreateView(AdminRequiredMixin, CreateView):
    """Create new network device."""
    template_name = 'assets/network_device_form.html'
    success_url = reverse_lazy('network_device_list')
    login_url = '/login/'
    
    def get_form_class(self):
        from assets.forms.asset_forms import NetworkDeviceForm
        return NetworkDeviceForm
    
    def form_valid(self, form):
        from assets.services.network_device_service import NetworkDeviceService
        
        try:
            data = {
                'device_type': form.cleaned_data['device_type'],
                'device_name': form.cleaned_data['device_name'],
                'ip_address_id': form.cleaned_data['ip_address'].id
            }
            device = NetworkDeviceService.create_network_device(data, self.request.user)
            messages.success(self.request, f'Network device {device.device_name} created successfully.')
            return redirect(self.success_url)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class NetworkDeviceUpdateView(AdminRequiredMixin, View):
    """Update existing network device."""
    template_name = 'assets/network_device_form.html'
    success_url = reverse_lazy('network_device_list')
    login_url = '/login/'
    
    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        from assets.models import NetworkDevice
        return get_object_or_404(NetworkDevice, pk=pk)
    
    def get(self, request, pk):
        from assets.forms.asset_forms import NetworkDeviceForm
        device = self.get_object(pk)
        form = NetworkDeviceForm(instance=device)
        return render(request, self.template_name, {'form': form, 'device': device})
    
    def post(self, request, pk):
        from assets.forms.asset_forms import NetworkDeviceForm
        from assets.services.network_device_service import NetworkDeviceService
        
        device = self.get_object(pk)
        form = NetworkDeviceForm(request.POST, instance=device)
        
        if form.is_valid():
            try:
                data = {
                    'device_type': form.cleaned_data['device_type'],
                    'device_name': form.cleaned_data['device_name'],
                    'ip_address_id': form.cleaned_data['ip_address'].id
                }
                updated_device = NetworkDeviceService.update_network_device(device, data, request.user)
                messages.success(request, f'Network device {updated_device.device_name} updated successfully.')
                return redirect(self.success_url)
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, str(e))
        else:
            messages.error(request, 'Please correct the errors below.')
        
        return render(request, self.template_name, {'form': form, 'device': device})


class NetworkDeviceDeleteView(AdminRequiredMixin, View):
    """Delete network device with confirmation."""
    login_url = '/login/'
    
    def get(self, request, pk):
        from django.shortcuts import get_object_or_404
        from assets.models import NetworkDevice
        device = get_object_or_404(NetworkDevice, pk=pk)
        return render(request, 'assets/network_device_confirm_delete.html', {'device': device})
    
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        from assets.models import NetworkDevice
        from assets.services.network_device_service import NetworkDeviceService
        
        device = get_object_or_404(NetworkDevice, pk=pk)
        device_name = device.device_name
        NetworkDeviceService.delete_network_device(device, request.user)
        messages.success(request, f'Network device {device_name} deleted successfully.')
        return redirect('network_device_list')
