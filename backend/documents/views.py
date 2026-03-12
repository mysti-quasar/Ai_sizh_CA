from rest_framework import generics, status, parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DocumentFolder, DocumentFile
from .serializers import DocumentFolderSerializer, DocumentFileSerializer


class ActiveClientMixin:
    """Mixin to scope queries to the user's active client profile."""

    def get_active_client(self):
        client = self.request.user.active_client_profile
        if not client:
            return None
        return client


class DocumentFolderListView(ActiveClientMixin, generics.ListAPIView):
    serializer_class = DocumentFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return DocumentFolder.objects.none()
        return DocumentFolder.objects.filter(client_profile=client, parent__isnull=True)


class DocumentFolderCreateView(ActiveClientMixin, generics.CreateAPIView):
    serializer_class = DocumentFolderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        client = self.get_active_client()
        serializer.save(client_profile=client)


class DocumentFolderDetailView(ActiveClientMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return DocumentFolder.objects.none()
        return DocumentFolder.objects.filter(client_profile=client)


class DocumentFileListView(ActiveClientMixin, generics.ListAPIView):
    serializer_class = DocumentFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return DocumentFile.objects.none()
        folder_id = self.kwargs.get("folder_id")
        return DocumentFile.objects.filter(folder__client_profile=client, folder_id=folder_id)


class DocumentFileUploadView(ActiveClientMixin, generics.CreateAPIView):
    serializer_class = DocumentFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        client = self.get_active_client()
        folder_id = self.kwargs.get("folder_id")
        try:
            folder = DocumentFolder.objects.get(pk=folder_id, client_profile=client)
        except DocumentFolder.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Folder not found or does not belong to active client.")

        uploaded_file = self.request.FILES.get("file")
        if not uploaded_file:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No file was provided.")

        # Detect file type from extension
        ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else "other"
        type_map = {"pdf": "pdf", "jpg": "image", "jpeg": "image", "png": "image",
                    "xlsx": "excel", "xls": "excel", "csv": "csv"}
        file_type = type_map.get(ext, "other")

        serializer.save(
            folder=folder,
            uploaded_by=self.request.user,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=file_type,
        )


class DocumentFileDetailView(ActiveClientMixin, generics.RetrieveDestroyAPIView):
    serializer_class = DocumentFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return DocumentFile.objects.none()
        return DocumentFile.objects.filter(folder__client_profile=client)


class InitDefaultFoldersView(ActiveClientMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = self.get_active_client()
        if not client:
            return Response({"error": "No active client"}, status=status.HTTP_400_BAD_REQUEST)
        DocumentFolder.create_defaults_for_client(client)
        folders = DocumentFolder.objects.filter(client_profile=client, parent__isnull=True)
        return Response(DocumentFolderSerializer(folders, many=True).data, status=status.HTTP_201_CREATED)
