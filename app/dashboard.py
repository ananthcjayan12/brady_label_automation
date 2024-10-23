from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from .models import Label

@staff_member_required
def dashboard(request):
    total_labels = Label.objects.count()
    printed_labels = Label.objects.filter(is_printed=True).count()
    first_stage_labels = Label.objects.filter(stage='first').count()
    second_stage_labels = Label.objects.filter(stage='second').count()

    labels_by_day = Label.objects.extra(select={'day': 'date(created_at)'}).values('day').annotate(count=Count('id')).order_by('-day')[:7]

    context = {
        'total_labels': total_labels,
        'printed_labels': printed_labels,
        'first_stage_labels': first_stage_labels,
        'second_stage_labels': second_stage_labels,
        'labels_by_day': labels_by_day,
    }
    return render(request, 'admin/dashboard.html', context)
