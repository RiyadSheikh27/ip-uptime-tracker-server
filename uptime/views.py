from django.views.generic import TemplateView
from rest_framework import generics

from .models import UptimeIP
from .serializers import UptimeIPSerializer


class DashboardView(TemplateView):
    """Simple status dashboard; the IP list comes from the environment."""
    template_name = 'uptime/index.html'


class UptimeListCreateView(generics.ListAPIView):
    """Read only list of the currently monitored IPs."""
    serializer_class = UptimeIPSerializer

    def get_queryset(self):
        return UptimeIP.objects.all()


class UptimeDetailView(generics.RetrieveAPIView):
    """Read only details for one monitored IP."""
    queryset = UptimeIP.objects.all()
    serializer_class = UptimeIPSerializer
