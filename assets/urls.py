from django.urls import path
from django.views.generic import TemplateView
from .views import (
    AssetListView, AssetCreateView, AssetUpdateView, AssetFreeView, 
    FreeSystemsView, AssetScrapView, ScrappedItemsView, FreeIPsView, 
    WarrantyView, AssetImportView, AssetImportResultsView, AssetExportActiveView, 
    AssetExportFreedView, AssetExportScrappedView, FreeIPsExportView, GetSubTeamsView,
    OperatingSystemListView, AddOperatingSystemView, EditOperatingSystemView, DeleteOperatingSystemView,
    FreedSystemCreateView, FreedSystemEditView, AssetReassignView,
    NetworkDeviceListView, NetworkDeviceCreateView, NetworkDeviceUpdateView, NetworkDeviceDeleteView
)

urlpatterns = [
    path('', AssetListView.as_view(), name='asset_list'),
    path('create/', AssetCreateView.as_view(), name='asset_create'),
    path('<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_update'),
    path('<int:pk>/free/', AssetFreeView.as_view(), name='asset_free'),
    path('<int:pk>/reassign/', AssetReassignView.as_view(), name='asset_reassign'),
    path('freed/', FreeSystemsView.as_view(), name='freed_systems'),
    path('freed/create/', FreedSystemCreateView.as_view(), name='freed_system_create'),
    path('freed/<int:pk>/edit/', FreedSystemEditView.as_view(), name='freed_system_edit'),
    path('<int:pk>/scrap/', AssetScrapView.as_view(), name='asset_scrap'),
    path('scrapped/', ScrappedItemsView.as_view(), name='scrapped_items'),
    path('ips/free/', FreeIPsView.as_view(), name='free_ips'),
    path('warranty/', WarrantyView.as_view(), name='warranty'),
    path('import/', AssetImportView.as_view(), name='asset_import'),
    path('import/results/', AssetImportResultsView.as_view(), name='asset_import_results'),
    path('export/active/', AssetExportActiveView.as_view(), name='export_active_assets'),
    path('export/freed/', AssetExportFreedView.as_view(), name='export_freed_assets'),
    path('export/scrapped/', AssetExportScrappedView.as_view(), name='export_scrapped_assets'),
    path('ips/export/free/', FreeIPsExportView.as_view(), name='export_free_ips'),
    path('api/get-sub-teams/', GetSubTeamsView.as_view(), name='get_sub_teams'),
    path('operating-systems/', OperatingSystemListView.as_view(), name='operating_systems'),
    path('operating-systems/add/', AddOperatingSystemView.as_view(), name='add_operating_system'),
    path('operating-systems/<int:pk>/edit/', EditOperatingSystemView.as_view(), name='edit_operating_system'),
    path('operating-systems/<int:pk>/delete/', DeleteOperatingSystemView.as_view(), name='delete_operating_system'),
    path('network-devices/', NetworkDeviceListView.as_view(), name='network_device_list'),
    path('network-devices/create/', NetworkDeviceCreateView.as_view(), name='network_device_create'),
    path('network-devices/<int:pk>/edit/', NetworkDeviceUpdateView.as_view(), name='network_device_update'),
    path('network-devices/<int:pk>/delete/', NetworkDeviceDeleteView.as_view(), name='network_device_delete'),
    path('test-reassign/', TemplateView.as_view(template_name='assets/test_reassign.html'), name='test_reassign'),
]
