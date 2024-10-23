from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import HomeView, FirstStageView, SecondStageView, process_barcode, DashboardView, preview_label, reprint_label

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('first-stage/', login_required(FirstStageView.as_view()), name='first_stage'),
    path('second-stage/', login_required(SecondStageView.as_view()), name='second_stage'),
    path('process-barcode/', process_barcode, name='process_barcode'),
    path('dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    path('preview-label/<int:label_id>/', preview_label, name='preview_label'),
    path('reprint-label/<int:label_id>/', reprint_label, name='reprint_label'),
]
