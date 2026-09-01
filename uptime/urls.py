from django.urls import path

from .views import UptimeListCreateView, UptimeDetailView, DashboardView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('uptime/', UptimeListCreateView.as_view(), name='uptime-list'),
    path('uptime/<int:pk>/', UptimeDetailView.as_view(), name='uptime-detail'),
]
