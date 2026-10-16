from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from motorpool.models import VehicleRequest


@login_required
def live_map(request):
    ongoing = VehicleRequest.objects.filter(status='ongoing')
    return render(request, 'tracking/live_map.html', {'ongoing': ongoing})


@login_required
def trip_history(request, pk):
    req = get_object_or_404(VehicleRequest, pk=pk)
    trip_log = getattr(req, 'trip_log', None)
    points = []
    if trip_log:
        points = list(trip_log.points.values('latitude', 'longitude', 'timestamp', 'note', 'stop_duration_min'))
    context = {
        'req': req,
        'trip_log': trip_log,
        'points': points,
    }
    return render(request, 'tracking/trip_history.html', context)