from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .views import HomeView, FirstStageView, SecondStageView, process_barcode, DashboardView, preview_label, SignUpView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('first-stage/', login_required(FirstStageView.as_view()), name='first_stage'),
    path('second-stage/', login_required(SecondStageView.as_view()), name='second_stage'),
    path('process-barcode/', login_required(process_barcode), name='process_barcode'),
    path('dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    path('preview-label/<int:label_id>/', login_required(preview_label), name='preview_label'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
]
