from django.urls import path
from .views import HomeView, FirstStageView, SecondStageView, process_barcode

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('first-stage/', FirstStageView.as_view(), name='first_stage'),
    path('second-stage/', SecondStageView.as_view(), name='second_stage'),
    path('process-barcode/', process_barcode, name='process_barcode'),
]
