from django.contrib import admin
from .models import (
    Vehicle,
    Driver,
    Barangay,
    VehicleRequest,
    TripLog,
    TripPoint,
)


# ============================================================
# VEHICLE ADMIN
# ============================================================

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'plate_number',
        'brand',
        'model',
        'vehicle_type',
        'capacity',
        'status',
        'created_at',
    )
    list_filter = ('status', 'vehicle_type', 'brand')
    search_fields = ('plate_number', 'brand', 'model', 'vehicle_type')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


# ============================================================
# DRIVER ADMIN
# ============================================================

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'license_number',
        'phone',
        'is_available',
        'user',
    )
    list_filter = ('is_available',)
    search_fields = ('name', 'license_number', 'phone')
    ordering = ('name',)


# ============================================================
# BARANGAY ADMIN
# ============================================================

@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'municipality')
    list_filter = ('municipality',)
    search_fields = ('name', 'municipality')
    ordering = ('municipality', 'name')


# ============================================================
# VEHICLE REQUEST ADMIN
# ============================================================

@admin.register(VehicleRequest)
class VehicleRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'requested_by',
        'department',
        'destination_municipality',
        'destination_barangay',
        'trip_type',
        'date_needed',
        'time_departure',
        'status',
    )
    list_filter = (
        'status',
        'trip_type',
        'department',
        'destination_municipality',
        'date_needed',
    )
    search_fields = (
        'requested_by__username',
        'requested_by__first_name',
        'requested_by__last_name',
        'purpose',
        'destination_municipality',
        'destination_barangay',
        'destination_address',
        'passenger_names',
    )
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'approved_at',
        'dispatcher_signed_at',
        'division_supervisor_signed_at',
        'department_manager_signed_at',
        'general_manager_signed_at',
        'guard_cleared_at',
        'actual_time_out',
        'actual_time_in',
    )
    date_hierarchy = 'date_needed'

    fieldsets = (
        ('Requester Information', {
            'fields': (
                'requested_by',
                'department',
                'date_filed',
            )
        }),
        ('Trip Details', {
            'fields': (
                'purpose',
                'trip_type',
                'date_needed',
                'time_departure',
                'time_return',
                'number_of_hours',
                'estimated_return_date',
            )
        }),
        ('Destination & Pickup', {
            'fields': (
                'destination_municipality',
                'destination_barangay',
                'destination_address',
                'pickup_location',
            )
        }),
        ('Passengers', {
            'fields': (
                'number_of_passengers',
                'passenger_names',
            )
        }),
        ('Assignment (Motorpool)', {
            'fields': (
                'vehicle',
                'driver',
                'assigned_by',
                'motorpool_notes',
            )
        }),
        ('Signature Chain - Authorized By', {
            'fields': (
                'dispatcher_name',
                'dispatcher_signed_at',
                'division_supervisor_name',
                'division_supervisor_signed_at',
                'department_manager_name',
                'department_manager_signed_at',
            )
        }),
        ('Approved By', {
            'fields': (
                'general_manager_name',
                'general_manager_signed_at',
            )
        }),
        ('Cleared By', {
            'fields': (
                'guard_on_duty_name',
                'guard_cleared_at',
            )
        }),
        ('Time Out / Time In', {
            'fields': (
                'actual_time_out',
                'actual_time_in',
            )
        }),
        ('Status & Timestamps', {
            'fields': (
                'status',
                'created_at',
                'updated_at',
                'approved_at',
            )
        }),
    )


# ============================================================
# TRIP LOG ADMIN
# ============================================================

@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'vehicle_request',
        'driver',
        'started_at',
        'ended_at',
        'total_distance_km',
    )
    list_filter = ('started_at', 'ended_at')
    search_fields = (
        'vehicle_request__id',
        'driver__name',
    )
    ordering = ('-started_at',)
    readonly_fields = ('started_at',)


# ============================================================
# TRIP POINT ADMIN
# ============================================================

@admin.register(TripPoint)
class TripPointAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'trip_log',
        'latitude',
        'longitude',
        'speed_kmh',
        'is_stop',
        'stop_duration_min',
        'barangay',
        'timestamp',
    )
    list_filter = ('is_stop', 'barangay', 'timestamp')
    search_fields = (
        'barangay',
        'note',
    )
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)