from django.urls import path
from .views import AssetListView, AssetCreateView, AssetUpdateView, AssetFreeView, FreeSystemsView, AssetScrapView, ScrappedItemsView, FreeIPsView, WarrantyView

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
]
