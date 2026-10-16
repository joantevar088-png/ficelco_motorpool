from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('motorpool', 'Motorpool Staff'),
        ('department', 'Department Employee'),
    )
    DEPARTMENTS = (
        ('admin_office', 'Admin Office'),
        ('engineering', 'Engineering'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('customer_service', 'Customer Service'),
        ('hr', 'Human Resources'),
        ('it', 'IT Department'),
        ('maintenance', 'Maintenance'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='department')
    department = models.CharField(max_length=50, choices=DEPARTMENTS, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    @property
    def is_admin_role(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_motorpool(self):
        return self.role == 'motorpool'

    @property
    def is_department(self):
        return self.role == 'department'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"