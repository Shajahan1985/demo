from django.urls import path
from django.views.generic import RedirectView
from .views import (
    LoginView, LogoutView, dashboard_view,
    UserListView, UserCreateView, UserUpdateView,
    user_deactivate, user_reactivate,
    assign_permission_to_user, revoke_permission_from_user,
    RoleListView, RoleCreateView, RoleUpdateView,
    PasswordResetRequestView, PasswordResetConfirmView
)

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False), name='root_redirect'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Password reset URLs
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User management URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/deactivate/', user_deactivate, name='user_deactivate'),
    path('users/<int:pk>/reactivate/', user_reactivate, name='user_reactivate'),
    path('users/<int:user_pk>/permissions/<int:permission_pk>/assign/', assign_permission_to_user, name='assign_permission'),
    path('users/<int:user_pk>/permissions/<int:permission_pk>/revoke/', revoke_permission_from_user, name='revoke_permission'),
    
    # Role management URLs
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', RoleUpdateView.as_view(), name='role_update'),
]
