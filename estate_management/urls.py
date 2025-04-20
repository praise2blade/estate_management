from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from visitors import views
from visitors.views import set_dues, view_dependent

urlpatterns = [
    # Admin site# API Endpoints (inside urls.py)
    path('api/visitor-requests/', views.visitor_requests_api, name='visitor_requests_api'),
    path('api/residents/', views.residents_api, name='residents_api'),
    path('api/landlords/', views.landlords_api, name='landlords_api'),

    path('admin/', admin.site.urls),

    # Authentication & Account
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path("accounts/", include("django.contrib.auth.urls")),

    # Home, Rules, Contact, Password Reset
    path('', views.home, name='home'),
    path('rules/', views.rules, name='rules'),
    path('contact-admin/', views.contact_admin, name='contact_admin'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('resident-dashboard/', views.resident_dashboard, name='resident_dashboard'),
    path('security-dashboard/', views.security_dashboard, name='security_dashboard'),
    path('landlord-dashboard/', views.landlord_dashboard, name='landlord_dashboard'),

    # Registration
    path('register-resident/', views.register_resident, name='register_resident'),
    path('register-landlord/', views.register_landlord, name='register_landlord'),
    path('register-house/', views.register_house, name='register_house'),
    path('register-street/', views.register_street, name='register_street'),

    # Lists
    path('residents/', views.resident_list, name='resident_list'),
    path('landlords/', views.landlord_list, name='landlord_list'),

    # AJAX
    path('get-houses/', views.get_houses, name='get_houses'),

    # Visitor Requests + Approvals + Checkouts
    path('visitor-history/', views.visitor_history, name='visitor_history'),
    path('raise-visitor-request/', views.raise_visitor_request, name='raise_visitor_request'),
    path('approve-visitor/<int:visitor_id>/', views.approve_visitor, name='approve_visitor'),
    path('reject-visitor/<int:visitor_id>/', views.reject_visitor, name='reject_visitor'),
    path('checkout-visitor/<int:visitor_id>/', views.checkout_visitor, name='checkout_visitor'),
    path('checkin-visitor/<int:visitor_id>/', views.checkin_visitor, name='checkin_visitor'),
    path('verify-visitor/', views.verify_visitor_code, name='verify_visitor_code'),

    # API Endpoints (inside urls.py)
    path('api/visitor-requests/', views.visitor_requests_api, name='visitor_requests_api'),
    path('api/residents/', views.residents_api, name='residents_api'),
    path('api/landlords/', views.landlords_api, name='landlords_api'),

    # Payments
    path('make-payment/', views.make_payment, name='make_payment'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('set-dues/', set_dues, name='set_dues'),

    # dependents
    path('resident-dependents/', views.resident_dependents, name='resident_dependents'),
    path('admin-residents-dependents/', views.admin_residents_and_dependents, name='admin_residents_dependents'),
    path('add-dependent/', views.add_dependent, name='add_dependent'),
    path('view-dependent/', view_dependent.as_view(), name='view_dependent')
]
