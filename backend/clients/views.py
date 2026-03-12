from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import ClientProfile
from .serializers import ClientProfileSerializer, ClientProfileListSerializer, ClientSearchSerializer


class ClientProfileListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClientProfileListSerializer
        return ClientProfileSerializer

    def get_queryset(self):
        # Return all client profiles in the system so every CA user
        # can see and switch to any client (shared CA firm pool).
        return ClientProfile.objects.all().order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClientProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientProfile.objects.filter(user=self.request.user)


class SwitchActiveClientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Accept either 'client_profile_id' (frontend store) or 'client_id'
        client_id = (
            request.data.get("client_profile_id")
            or request.data.get("client_id")
        )
        if not client_id:
            return Response(
                {"error": "client_profile_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            client = ClientProfile.objects.get(id=client_id)
        except ClientProfile.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        request.user.active_client_profile = client
        request.user.save(update_fields=["active_client_profile"])
        return Response({"active_client": ClientProfileSerializer(client).data})


class ActiveClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.active_client_profile
        if not client:
            return Response({"active_client": None}, status=status.HTTP_200_OK)
        return Response({"active_client": ClientProfileSerializer(client).data})


class ClientSearchView(generics.ListAPIView):
    """Search clients by name, trade name, PAN, GSTIN, or phone.

    GET /api/clients/search/?q=<term>
    """
    serializer_class = ClientSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        qs = ClientProfile.objects.all()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(trade_name__icontains=q)
                | Q(pan__icontains=q)
                | Q(gstin__icontains=q)
                | Q(phone__icontains=q)
            )
        return qs.order_by("name")
