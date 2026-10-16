from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    return redirect(notif.link or 'notification_list')