from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
from django.utils import timezone

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('resident', 'Resident'),
    ('landlord', 'Landlord'),
    ('security', 'Security'),
)

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def is_resident(self):
        return self.role == 'resident'

    def is_landlord(self):
        return self.role == 'landlord'

    def is_security(self):
        return self.role == 'security'

    def is_admin(self):
        return self.role == 'admin'

class Landlord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='landlord_profile')
    def __str__(self):
        return self.user.username

class Street(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}, {self.city or ''} {self.state or ''}"

class House(models.Model):
    number = models.CharField(max_length=100)
    street = models.ForeignKey(Street, on_delete=models.SET_NULL, null=True, blank=True)
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='houses')

    def __str__(self):
        return f"{self.number} - {self.street}"

class Resident(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident_profile')
    landlord = models.ForeignKey('Landlord', on_delete=models.CASCADE, related_name='residents')
    house = models.ForeignKey('House', on_delete=models.CASCADE, related_name='residents')
    unique_code = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.unique_code:
            last_id = Resident.objects.count() + 1
            self.unique_code = f"SERA-{last_id:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username
    
class VisitorRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
    )

    visitor_name = models.CharField(max_length=100)
    purpose = models.TextField()
    unique_code = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visitor_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    raised_by = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('resident', 'Resident')])
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    resident_approved = models.BooleanField(default=False)


    def is_expired(self):
        return timezone.now() > self.expires_at

    def generate_unique_code(self, length=10):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def save(self, *args, **kwargs):
        if not self.unique_code:
            self.unique_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class Dues(models.Model):
    resident_due = models.DecimalField(max_digits=10, decimal_places=2)
    landlord_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Resident: {self.resident_due} | Landlord: {self.landlord_due}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    months_paid_for = models.PositiveIntegerField()
    payment_date = models.DateField(auto_now_add=True)
    due = models.ForeignKey(Dues, on_delete=models.SET_NULL, null=True)
    receipt = models.FileField(upload_to='payments/receipts/', null=True, blank=True)  # Receipt upload field
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    year = models.PositiveIntegerField(default=timezone.now().year)

    def __str__(self):
        return f"Payment of {self.amount} for {self.months_paid_for} months"


DEPENDENT_TYPE_CHOICES = (
    ('child', 'Child'),
    ('wife', 'Wife'),
    ('husband', 'Husband'),
    ('brother', 'Brother'),
    ('sister', 'Sister'),
)

class Dependent(models.Model):
    resident = models.ForeignKey('Resident', on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100)
    dependent_type = models.CharField(max_length=20, choices=DEPENDENT_TYPE_CHOICES)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    unique_code = models.CharField(max_length=30, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.unique_code:
            dependent_count = Dependent.objects.filter(resident=self.resident).count() + 1
            suffix = ''
            if self.dependent_type == 'child':
                suffix = f'C{dependent_count}'
            elif self.dependent_type == 'wife':
                suffix = 'W'
            elif self.dependent_type == 'husband':
                suffix = 'H'
            elif self.dependent_type == 'brother':
                suffix = f'B{dependent_count}'
            elif self.dependent_type == 'sister':
                suffix = f'S{dependent_count}'
            self.unique_code = f"{self.resident.unique_code}-{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.dependent_type})"


