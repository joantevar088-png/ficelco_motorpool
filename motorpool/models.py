from django.db import models
from django.conf import settings
from django.utils import timezone


class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
    )
    plate_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    capacity = models.IntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plate_number} - {self.brand} {self.model}"


class Driver(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Barangay(models.Model):
    """Listahan ng mga barangay per municipality"""
    municipality = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['municipality', 'name']
        unique_together = ('municipality', 'name')

    def __str__(self):
        return f"{self.name}, {self.municipality}"


class VehicleRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )

    TRIP_TYPE_CHOICES = (
        ('official', 'Official'),
        ('personal', 'Personal'),
    )

    # ===== REQUESTER INFO =====
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
    department = models.CharField(max_length=100)
    date_filed = models.DateTimeField(auto_now_add=True)

    # ===== TRIP DETAILS =====
    purpose = models.TextField(help_text='Purpose of the trip')
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='official')

    # Destination with municipality + barangay filtering
    destination_municipality = models.CharField(max_length=100)
    destination_barangay = models.CharField(max_length=100)
    destination_address = models.CharField(max_length=255, blank=True, null=True, help_text='Specific address/landmark')
    pickup_location = models.CharField(max_length=255)

    # Passengers
    number_of_passengers = models.IntegerField(default=1)
    passenger_names = models.TextField(blank=True, null=True, help_text='List of passenger names (one per line)')

    # Time details
    date_needed = models.DateField()
    time_departure = models.TimeField()
    time_return = models.TimeField()
    number_of_hours = models.IntegerField(default=1, help_text='Total hours needed')
    estimated_return_date = models.DateField(null=True, blank=True)

    # ===== ASSIGNMENT (Motorpool) =====
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_requests',
        help_text='Motorpool staff who approved/assigned'
    )
    motorpool_notes = models.TextField(blank=True, null=True)

    # ===== SIGNATURE CHAIN =====
    # Authorized by
    dispatcher_name = models.CharField(max_length=100, blank=True, null=True)
    dispatcher_signed_at = models.DateTimeField(null=True, blank=True)

    division_supervisor_name = models.CharField(max_length=100, blank=True, null=True)
    division_supervisor_signed_at = models.DateTimeField(null=True, blank=True)

    department_manager_name = models.CharField(max_length=100, blank=True, null=True)
    department_manager_signed_at = models.DateTimeField(null=True, blank=True)

    # Approved by (General Manager)
    general_manager_name = models.CharField(max_length=100, default='Francis Gianan', blank=True, null=True)
    general_manager_signed_at = models.DateTimeField(null=True, blank=True)

    # Cleared by (Guard on duty)
    guard_on_duty_name = models.CharField(max_length=100, blank=True, null=True)
    guard_cleared_at = models.DateTimeField(null=True, blank=True)

    # ===== TIME OUT / TIME IN =====
    actual_time_out = models.DateTimeField(null=True, blank=True)
    actual_time_in = models.DateTimeField(null=True, blank=True)

    # ===== STATUS =====
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request #{self.id} - {self.requested_by.username}"

    @property
    def destination_full(self):
        parts = [self.destination_barangay, self.destination_municipality]
        if self.destination_address:
            parts.insert(0, self.destination_address)
        return ', '.join([p for p in parts if p])

    @property
    def is_fully_approved(self):
        return all([
            self.dispatcher_signed_at,
            self.division_supervisor_signed_at,
            self.department_manager_signed_at,
            self.general_manager_signed_at,
        ])


class TripLog(models.Model):
    vehicle_request = models.OneToOneField(VehicleRequest, on_delete=models.CASCADE, related_name='trip_log')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_distance_km = models.FloatField(default=0)

    def __str__(self):
        return f"Trip for Request #{self.vehicle_request.id}"


class TripPoint(models.Model):
    trip_log = models.ForeignKey(TripLog, on_delete=models.CASCADE, related_name='points')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    speed_kmh = models.FloatField(default=0)
    stop_duration_min = models.FloatField(default=0, help_text='Stop duration if vehicle was stationary')
    is_stop = models.BooleanField(default=False, help_text='True if vehicle stopped for 10+ minutes')
    note = models.CharField(max_length=200, blank=True, null=True)
    barangay = models.CharField(max_length=100, blank=True, null=True, help_text='Barangay where the point is')

    class Meta:
        ordering = ['timestamp']