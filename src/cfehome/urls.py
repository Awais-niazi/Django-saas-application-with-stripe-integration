"""
URL configuration for cfehome project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from auth import views as auth_views
urlpatterns = [
    path("", views.landing_page_view, name= 'landing_page'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.login_view, name='login_view'),
    path('logout/', auth_views.logout_view, name='logout_view'),
    path('register/', auth_views.register_view, name='register_view'),
    path('home/', views.home_view, name= 'home_view' ),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
    path('about/', views.about_view, name= 'about_views'),
    path('features/', views.about_view, name='features_view'),
    path('pricing/', views.pricing_view, name='pricing_view'),
    path('onboarding/', views.onboarding_view, name='onboarding_view'),
    path('account-overview/', views.account_overview_view, name='account_overview_view'),
    path('billing/', views.billing_overview_view, name='billing_overview_view'),
    path('billing/success/', views.billing_success_view, name='billing_success_view'),
    path('billing/cancel/', views.billing_cancel_view, name='billing_cancel_view'),
    path('billing/portal/', views.billing_portal_view, name='billing_portal_view'),
    path('billing/checkout/<int:price_id>/', views.create_checkout_session_view, name='create_checkout_session_view'),
    path('support/', views.support_view, name='support_view'),
    path('privacy/', views.privacy_view, name='privacy_view'),
    path('terms/', views.terms_view, name='terms_view'),
    path('health/', views.health_check_view, name='health_check_view'),
    path('webhooks/stripe/', views.stripe_webhook_view, name='stripe_webhook_view'),
    path('protected/', views.pw_protected_view),
    path('protected/user-only/', views.user_only_view),
    path('protected/staff-only/', views.staff_only_view),
    path('accounts/', include('allauth.urls')),
    path('profiles/', include('profiles.urls')),

]
