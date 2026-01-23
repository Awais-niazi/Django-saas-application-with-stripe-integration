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
    path('login/', auth_views.login_view),
    path('register/', auth_views.register_view),
    path('home/', views.home_view, name= 'home_view' ),
    path('about/', views.about_view, name= 'about_views'),
    path('protected/', views.pw_protected_view),
    path('protected/user-only/', views.user_only_view),
    path('protected/staff-only/', views.staff_only_view),
    path('accounts/', include('allauth.urls')),
    path('profiles/', include('profiles.urls')),

]
