from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .models import (
    Vehicle, Driver, VehicleRequest, TripLog, TripPoint, Barangay
)
from accounts_app.models import CustomUser
from notifications.models import Notification


# ============================================================
# DASHBOARD VIEWS
# ============================================================

@login_required
def admin_dashboard(request):
    """Admin dashboard — overall statistics"""
    if not request.user.is_admin_role:
        return redirect('dashboard')

    all_requests = VehicleRequest.objects.all()

    context = {
        'total_users': CustomUser.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_drivers': Driver.objects.count(),
        'total_requests': all_requests.count(),
        'pending_requests': all_requests.filter(status='pending').count(),
        'approved_requests': all_requests.filter(status='approved').count(),
        'ongoing_trips': all_requests.filter(status='ongoing').count(),
        'completed_requests': all_requests.filter(status='completed').count(),
        'recent_requests': all_requests.order_by('-created_at')[:5],
    }
    return render(request, 'motorpool/admin_dashboard.html', context)


@login_required
def department_dashboard(request):
    """Department employee dashboard"""
    if request.user.role not in ['department', 'admin'] and not request.user.is_superuser:
        return redirect('motorpool_dashboard')

    my_requests = VehicleRequest.objects.filter(
        requested_by=request.user
    ).order_by('-created_at')

    stats = {
        'total': my_requests.count(),
        'pending': my_requests.filter(status='pending').count(),
        'approved': my_requests.filter(status='approved').count(),
        'ongoing': my_requests.filter(status='ongoing').count(),
        'completed': my_requests.filter(status='completed').count(),
    }

    context = {
        'requests': my_requests,
        'my_requests': my_requests,
        'stats': stats,
        'pending': stats['pending'],
        'approved': stats['approved'],
        'completed': stats['completed'],
    }
    return render(request, 'motorpool/department_dashboard.html', context)


@login_required
def motorpool_dashboard(request):
    """Motorpool staff dashboard"""
    if request.user.role not in ['motorpool', 'admin'] and not request.user.is_superuser:
        return redirect('department_dashboard')

    all_requests = VehicleRequest.objects.all().order_by('-created_at')

    stats = {
        'total': all_requests.count(),
        'pending': all_requests.filter(status='pending').count(),
        'approved': all_requests.filter(status='approved').count(),
        'ongoing': all_requests.filter(status='ongoing').count(),
        'completed': all_requests.filter(status='completed').count(),
    }

    context = {
        'requests': all_requests,
        'pending_requests': all_requests.filter(status='pending'),
        'ongoing_trips': all_requests.filter(status='ongoing'),
        'stats': stats,
        'available_vehicles': Vehicle.objects.filter(status='available'),
        'available_drivers': Driver.objects.filter(is_available=True),
    }
    return render(request, 'motorpool/motorpool_dashboard.html', context)


# ============================================================
# VEHICLE REQUEST - CREATE
# ============================================================

@login_required
def create_request(request):
    if request.method == 'POST':
        purpose = request.POST.get('purpose')
        trip_type = request.POST.get('trip_type', 'official')
        destination_municipality = request.POST.get('destination_municipality')
        destination_barangay = request.POST.get('destination_barangay')
        destination_address = request.POST.get('destination_address', '')
        pickup_location = request.POST.get('pickup_location', 'FICELCO Main Office, Marinawa, Bato')
        number_of_passengers = request.POST.get('number_of_passengers', 1)

        # Passenger names — getlist from multi-select
        passenger_list = request.POST.getlist('passenger_names')
        passenger_names_str = ', '.join(passenger_list) if passenger_list else ''

        date_needed = request.POST.get('date_needed')
        time_departure = request.POST.get('time_departure')
        time_return = request.POST.get('time_return')
        number_of_hours = request.POST.get('number_of_hours', 1)
        estimated_return_date = request.POST.get('estimated_return_date') or None

        if not all([purpose, destination_municipality, destination_barangay,
                    date_needed, time_departure, time_return]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_request')

        try:
            department = request.user.get_department_display()
        except Exception:
            department = request.user.department or 'N/A'

        req = VehicleRequest.objects.create(
            requested_by=request.user,
            department=department,
            purpose=purpose,
            trip_type=trip_type,
            destination_municipality=destination_municipality,
            destination_barangay=destination_barangay,
            destination_address=destination_address,
            pickup_location=pickup_location,
            number_of_passengers=int(number_of_passengers) if number_of_passengers else 1,
            passenger_names=passenger_names_str,
            date_needed=date_needed,
            time_departure=time_departure,
            time_return=time_return,
            number_of_hours=int(number_of_hours) if number_of_hours else 1,
            estimated_return_date=estimated_return_date,
            status='pending',
        )

        # Notify motorpool staff
        for staff in CustomUser.objects.filter(role='motorpool'):
            Notification.objects.create(
                recipient=staff,
                title='🚗 New Vehicle Request',
                message=f'{request.user.username} requested a vehicle to {req.destination_full} on {req.date_needed}',
                link=f'/motorpool/request/{req.id}/approve/'
            )

        # Notify admins
        for admin_user in CustomUser.objects.filter(role='admin'):
            Notification.objects.create(
                recipient=admin_user,
                title='🚗 New Vehicle Request',
                message=f'{request.user.username} ({department}) requested a vehicle to {req.destination_full}',
                link=f'/motorpool/request/{req.id}/approve/'
            )

        messages.success(request, f'✅ Vehicle request #{req.id} submitted! Waiting for motorpool approval.')
        return redirect('department_dashboard')

    # ===== GET — Filter employees by department =====
    user_dept = request.user.department
    user_role = request.user.role

    if user_role in ['admin', 'motorpool'] or not user_dept:
        # Admin/motorpool — show all employees
        employees = CustomUser.objects.filter(
            is_active=True
        ).exclude(id=request.user.id).order_by('first_name', 'last_name', 'username')
    else:
        # Department user — show only same department
        employees = CustomUser.objects.filter(
            is_active=True,
            department=user_dept
        ).exclude(id=request.user.id).order_by('first_name', 'last_name', 'username')

    context = {
        'employees': employees,
        'user_department': user_dept,
    }
    return render(request, 'motorpool/create_request.html', context)


# ============================================================
# VEHICLE REQUEST - VIEW DETAILS
# ============================================================

@login_required
def request_detail(request, pk=None, request_id=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.user.role == 'department' and req.requested_by != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('department_dashboard')

    trip_log = getattr(req, 'trip_log', None)
    trip_points = []
    if trip_log:
        trip_points = trip_log.points.all().order_by('timestamp')

    context = {
        'req': req,
        'available_vehicles': Vehicle.objects.filter(status='available'),
        'available_drivers': Driver.objects.filter(is_available=True),
        'trip_log': trip_log,
        'trip_points': trip_points,
    }
    return render(request, 'motorpool/request_detail.html', context)


# ============================================================
# MOTORPOOL - APPROVE & ASSIGN
# ============================================================

@login_required
def approve_request(request, pk=None, request_id=None):
    req_id = request_id or pk

    if request.user.role not in ['motorpool', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'Only motorpool staff can approve requests.')
        return redirect('department_dashboard')

    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            vehicle_id = request.POST.get('vehicle')
            driver_id = request.POST.get('driver')
            motorpool_notes = request.POST.get('motorpool_notes', '')

            if not vehicle_id or not driver_id:
                messages.error(request, 'Please select both vehicle and driver.')
                return redirect('approve_request', pk=req.id)

            vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            driver = get_object_or_404(Driver, id=driver_id)

            req.vehicle = vehicle
            req.driver = driver
            req.assigned_by = request.user
            req.motorpool_notes = motorpool_notes
            req.status = 'approved'
            req.approved_at = timezone.now()
            req.save()

            vehicle.status = 'in_use'
            vehicle.save()

            driver.is_available = False
            driver.save()

            Notification.objects.create(
                recipient=req.requested_by,
                title='✅ Vehicle Request Approved',
                message=f'Your request #{req.id} has been approved. Vehicle: {vehicle.plate_number}, Driver: {driver.name}',
                link=f'/motorpool/request/{req.id}/'
            )

            messages.success(request, f'✅ Request #{req.id} approved and assigned!')
            return redirect('request_detail', pk=req.id)

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'No reason provided')
            req.status = 'rejected'
            req.motorpool_notes = f'REJECTED: {reason}'
            req.save()

            Notification.objects.create(
                recipient=req.requested_by,
                title='❌ Vehicle Request Rejected',
                message=f'Your request #{req.id} was rejected. Reason: {reason}',
                link=f'/motorpool/request/{req.id}/'
            )

            messages.warning(request, f'Request #{req.id} rejected.')
            return redirect('motorpool_dashboard')

    context = {
        'req': req,
        'available_vehicles': Vehicle.objects.filter(status='available'),
        'available_drivers': Driver.objects.filter(is_available=True),
        'vehicles': Vehicle.objects.filter(status='available'),
        'drivers': Driver.objects.filter(is_available=True),
    }
    return render(request, 'motorpool/approve_request.html', context)


@login_required
def notify_pickup(request, pk=None, request_id=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, pk=req_id)

    Notification.objects.create(
        recipient=req.requested_by,
        title='🚗 Driver Arrived',
        message=f'Driver {req.driver.name if req.driver else "N/A"} is waiting outside {req.pickup_location}.',
        link=f'/motorpool/request/{req.id}/'
    )
    messages.success(request, f'Notification sent to {req.requested_by.username}')
    return redirect('motorpool_dashboard')


# ============================================================
# SIGNATURE CHAIN
# ============================================================

@login_required
def sign_dispatcher(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        name = request.POST.get('dispatcher_name', request.user.get_full_name() or request.user.username)
        req.dispatcher_name = name
        req.dispatcher_signed_at = timezone.now()
        req.save()

        messages.success(request, '✅ Dispatcher signature added.')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/sign_dispatcher.html', {'req': req})


@login_required
def sign_division_supervisor(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        name = request.POST.get('division_supervisor_name', request.user.get_full_name() or request.user.username)
        req.division_supervisor_name = name
        req.division_supervisor_signed_at = timezone.now()
        req.save()

        messages.success(request, '✅ Division Supervisor signature added.')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/sign_division_supervisor.html', {'req': req})


@login_required
def sign_department_manager(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        name = request.POST.get('department_manager_name', request.user.get_full_name() or request.user.username)
        req.department_manager_name = name
        req.department_manager_signed_at = timezone.now()
        req.save()

        messages.success(request, '✅ Department Manager signature added.')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/sign_department_manager.html', {'req': req})


@login_required
def sign_general_manager(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        req.general_manager_name = request.POST.get('general_manager_name', 'Francis Gianan')
        req.general_manager_signed_at = timezone.now()
        req.save()

        Notification.objects.create(
            recipient=req.requested_by,
            title='✅ Approved by General Manager',
            message=f'Your request #{req.id} has been approved by General Manager Francis Gianan.',
            link=f'/motorpool/request/{req.id}/'
        )

        messages.success(request, '✅ General Manager approval added.')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/sign_general_manager.html', {'req': req})


@login_required
def sign_guard_on_duty(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        req.guard_on_duty_name = request.POST.get('guard_on_duty_name', request.user.get_full_name() or request.user.username)
        req.guard_cleared_at = timezone.now()
        req.save()

        messages.success(request, '✅ Guard clearance added.')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/sign_guard.html', {'req': req})


# ============================================================
# TIME OUT / TIME IN
# ============================================================

@login_required
def time_out(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        req.actual_time_out = timezone.now()
        req.status = 'ongoing'
        req.save()

        if not hasattr(req, 'trip_log'):
            TripLog.objects.create(vehicle_request=req, driver=req.driver)

        if req.vehicle:
            req.vehicle.status = 'in_use'
            req.vehicle.save()

        messages.success(request, f'🕐 Time Out recorded for Request #{req.id}')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/time_out.html', {'req': req})


@login_required
def time_in(request, request_id=None, pk=None):
    req_id = request_id or pk
    req = get_object_or_404(VehicleRequest, id=req_id)

    if request.method == 'POST':
        req.actual_time_in = timezone.now()
        req.status = 'completed'
        req.save()

        if req.vehicle:
            req.vehicle.status = 'available'
            req.vehicle.save()

        if req.driver:
            req.driver.is_available = True
            req.driver.save()

        if hasattr(req, 'trip_log'):
            trip_log = req.trip_log
            trip_log.ended_at = timezone.now()
            trip_log.save()

        Notification.objects.create(
            recipient=req.requested_by,
            title='🏁 Trip Completed',
            message=f'Your vehicle request #{req.id} has been completed. Welcome back!',
            link=f'/motorpool/request/{req.id}/'
        )

        messages.success(request, f'🕐 Time In recorded for Request #{req.id}. Trip completed!')
        return redirect('request_detail', pk=req.id)

    return render(request, 'motorpool/time_in.html', {'req': req})


# ============================================================
# BARANGAY API
# ============================================================

@login_required
def get_barangays(request, municipality):
    barangays = Barangay.objects.filter(
        municipality__iexact=municipality
    ).values_list('name', flat=True).order_by('name')

    return JsonResponse({
        'municipality': municipality,
        'barangays': list(barangays)
    })


# ============================================================
# LIVE TRACKING
# ============================================================

@login_required
def live_map(request):
    if request.user.role not in ['motorpool', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('department_dashboard')

    active_trips = VehicleRequest.objects.filter(
        status='ongoing'
    ).select_related('vehicle', 'driver', 'requested_by')

    context = {
        'active_trips': active_trips,
        'ongoing': active_trips,
    }
    return render(request, 'tracking/live_map.html', context)


@login_required
def get_active_trips(request):
    active_trips = VehicleRequest.objects.filter(status='ongoing')

    data = []
    for trip in active_trips:
        trip_log = getattr(trip, 'trip_log', None)
        latest_point = None
        if trip_log:
            latest_point = trip_log.points.order_by('-timestamp').first()

        data.append({
            'id': trip.id,
            'vehicle': trip.vehicle.plate_number if trip.vehicle else 'N/A',
            'driver': trip.driver.name if trip.driver else 'N/A',
            'destination': trip.destination_full,
            'purpose': trip.purpose,
            'requested_by': trip.requested_by.get_full_name() or trip.requested_by.username,
            'date_needed': str(trip.date_needed),
            'time_departure': str(trip.time_departure),
            'latest_lat': latest_point.latitude if latest_point else None,
            'latest_lng': latest_point.longitude if latest_point else None,
            'last_update': latest_point.timestamp.isoformat() if latest_point else None,
        })

    return JsonResponse({'trips': data})


@login_required
def add_trip_point(request, trip_log_id):
    if request.method == 'POST':
        trip_log = get_object_or_404(TripLog, id=trip_log_id)

        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        speed_kmh = request.POST.get('speed_kmh', 0)
        barangay = request.POST.get('barangay', '')

        if latitude and longitude:
            TripPoint.objects.create(
                trip_log=trip_log,
                latitude=float(latitude),
                longitude=float(longitude),
                speed_kmh=float(speed_kmh) if speed_kmh else 0,
                barangay=barangay,
                is_stop=float(speed_kmh) < 2 if speed_kmh else False,
            )
            return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)


# ============================================================
# REQUEST LIST
# ============================================================

@login_required
def request_list(request):
    if request.user.role not in ['motorpool', 'admin'] and not request.user.is_superuser:
        return redirect('department_dashboard')

    status_filter = request.GET.get('status', 'all')
    reqs = VehicleRequest.objects.all().order_by('-created_at')

    if status_filter != 'all':
        reqs = reqs.filter(status=status_filter)

    context = {
        'requests': reqs,
        'status_filter': status_filter,
    }
    return render(request, 'motorpool/request_list.html', context)


@login_required
def my_requests(request):
    reqs = VehicleRequest.objects.filter(
        requested_by=request.user
    ).order_by('-created_at')

    context = {'requests': reqs}
    return render(request, 'motorpool/my_requests.html', context)