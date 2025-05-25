from django.urls import path, include
from . import views
from .views import complete_profile
app_name = 'vehicles'

urlpatterns = [
    path('', views.login_view, name='landing'),
    path('home/', views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('vehicle/<int:vehicle_id>/', views.vehicle_detail, name='vehicle_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('complete_profile/', views.complete_profile, name='complete_profile'),
    path('profile/', views.profile, name='profile'),
    path('account_login/', views.login_view, name='account_login'),
    path('account_signup/', views.test, name='account_signup'),
    path('manage_vehicles', views.manage_vehicles, name='manage_vehicles'),
    path('add_vehicle/', views.add_vehicle, name='add_vehicle'),
    path('edit_vehicle/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('delete_vehicle/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('manage/', views.manage_collections, name='manage_collections'),
    path('add/', views.add_collection, name='add_collection'),
    path('edit/<int:collection_id>/', views.edit_collection, name='edit_collection'),
    path('delete/<int:collection_id>/', views.delete_collection, name='delete_collection'),
    path('collection/<int:collection_id>/', views.collection_details, name='collection_details'),
    path('create_request/<int:collection_id>/', views.create_request, name='create_request'),
    path('approve_request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject_request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('guest-login/', views.guest_login, name='guest_login'),
    path('manage_librarians/', views.manage_librarians, name='manage_librarians'),
    path('promote/<int:user_id>/', views.promote_to_librarian, name='promote_to_librarian'),
    path('borrow_vehicle/<int:vehicle_id>/', views.borrow_vehicle, name='borrow_vehicle'),
    path('approve_borrow/<int:request_id>/', views.approve_borrow, name='approve_borrow'),
    path('reject_borrow/<int:request_id>/', views.reject_borrow, name='reject_borrow'),
    path('manage_requests', views.manage_requests, name='manage_requests'),
]