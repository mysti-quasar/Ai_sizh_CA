"""
SIZH CA - Document Vault URL Configuration
============================================
"""

from django.urls import path
from .views import (
    DocumentFolderListView,
    DocumentFolderCreateView,
    DocumentFolderDetailView,
    DocumentFileListView,
    DocumentFileUploadView,
    DocumentFileDetailView,
    InitDefaultFoldersView,
)

app_name = "documents"

urlpatterns = [
    # Folders
    path("folders/", DocumentFolderListView.as_view(), name="folder_list"),
    path("folders/create/", DocumentFolderCreateView.as_view(), name="folder_create"),
    path("folders/<uuid:pk>/", DocumentFolderDetailView.as_view(), name="folder_detail"),
    # Files within folders
    path(
        "folders/<uuid:folder_id>/files/",
        DocumentFileListView.as_view(),
        name="file_list",
    ),
    path(
        "folders/<uuid:folder_id>/files/upload/",
        DocumentFileUploadView.as_view(),
        name="file_upload",
    ),
    # Single file operations
    path("files/<uuid:pk>/", DocumentFileDetailView.as_view(), name="file_detail"),
    # Initialize defaults
    path("init-folders/", InitDefaultFoldersView.as_view(), name="init_folders"),
]
