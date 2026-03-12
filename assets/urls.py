from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetUpdateView, AssetFreeView, 
    FreeSystemsView, AssetScrapView, ScrappedItemsView, FreeIPsView, 
    WarrantyView, AssetImportView, AssetImportResultsView, AssetExportActiveView, 
    AssetExportFreedView, AssetExportScrappedView, FreeIPsExportView, GetSubTeamsView
)

urlpatterns = [
    path('', AssetListView.as_view(), name='asset_list'),
    path('create/', AssetCreateView.as_view(), name='asset_create'),
    path('<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_update'),
    path('<int:pk>/free/', AssetFreeView.as_view(), name='asset_free'),
    path('freed/', FreeSystemsView.as_view(), name='freed_systems'),
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
]
