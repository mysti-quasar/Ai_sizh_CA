"""
SIZH CA - Client Profile URL Configuration
============================================
"""

from django.urls import path
from .views import (
    ClientProfileListCreateView,
    ClientProfileDetailView,
    SwitchActiveClientView,
    ActiveClientView,
    ClientSearchView,
)

app_name = "clients"

urlpatterns = [
    path("", ClientProfileListCreateView.as_view(), name="list_create"),
    path("search/", ClientSearchView.as_view(), name="search"),
    path("<uuid:pk>/", ClientProfileDetailView.as_view(), name="detail"),
    path("switch/", SwitchActiveClientView.as_view(), name="switch_active"),
    path("active/", ActiveClientView.as_view(), name="active"),
]
