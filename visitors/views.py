from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from .models import User, Landlord, Resident, House, Street, VisitorRequest, Dues, Payment, Dependent
from .forms import CustomUserCreationForm, LandlordCreationForm, HouseForm, StreetForm, DuesForm, DependentForm
from datetime import timedelta
from django.utils import timezone
from collections import defaultdict
import random
import string
from .forms import VisitorRequestForm, PaymentForm
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from .models import VisitorRequest, Resident, Landlord
from twilio.rest import Client
from .utils import generate_unique_code, send_sms



channel_layer = get_channel_layer()

def home(request):
    return render(request, 'home.html')

def rules(request):
    return render(request, 'rules.html')

def contact_admin(request):
    return render(request, 'contact_admin.html')

def password_reset(request):
    return render(request, 'password_reset.html')

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

def password_reset_confirm(request, uidb64, token): 
    return render(request, 'password_reset_confirm.html', {'uidb64': uidb64, 'token': token})

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')

def visitor_requests_api(request):
    visitor_requests = VisitorRequest.objects.all().values('visitor_name', 'status', 'resident__username', 'created_at')
    return JsonResponse(list(visitor_requests), safe=False)

def residents_api(request):
    residents = Resident.objects.all().values('user__username', 'house__number', 'landlord__user__username')
    return JsonResponse(list(residents), safe=False)

def landlords_api(request):
    landlords = Landlord.objects.all().values('user__username', 'user__email', 'user__phone_number')
    return JsonResponse(list(landlords), safe=False)

def dashboard(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'landlord_profile'):
            return redirect('landlord_dashboard')
        elif hasattr(request.user, 'resident_profile'):
            return redirect('resident_dashboard')
    return render(request, 'dashboard.html')


class CustomLoginView(auth_views.LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, "Login successful.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid credentials. Please try again.")
        return super().form_invalid(form)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'months_paid_for', 'payment_date', 'status', 'receipt']
    list_filter = ['status']
    actions = ['approve_payment', 'reject_payment']

    def approve_payment(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected payments have been approved.")

    def reject_payment(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected payments have been rejected.")

admin.site.register(Payment, PaymentAdmin)

from django.db.models import Q

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    query = request.GET.get('q', '')

    visitor_requests = VisitorRequest.objects.all().order_by('-created_at')

    if query:
        visitor_requests = visitor_requests.filter(unique_code__icontains=query)

    return render(request, 'admin_dashboard.html', {
        'visitor_requests': visitor_requests,
        'query': query
    })


@login_required
def security_dashboard(request):
    if not request.user.is_security_guard:
        raise PermissionDenied()

    query = request.GET.get('q', '')

    visitor_requests = VisitorRequest.objects.exclude(status='checked_out').order_by('-created_at')

    if query:
        visitor_requests = visitor_requests.filter(unique_code__icontains=query)

    return render(request, 'admin_dashboard.html', {
        'visitor_requests': visitor_requests,
        'query': query
    })



@login_required
def register_street(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        form = StreetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Street registered successfully.")
            return redirect('admin_dashboard')
    else:
        form = StreetForm()

    return render(request, 'register_street.html', {'form': form})

@login_required
def register_house(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        form = HouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "House registered successfully.")
            return redirect('admin_dashboard')
    else:
        form = HouseForm()

    return render(request, 'register_house.html', {'form': form})


@login_required
def register_landlord(request):
    if request.method == 'POST':
        form = LandlordCreationForm(request.POST)
        print("Form received:", form.data)
        if form.is_valid():
            print("Form valid.")
            user = form.save(commit=False)
            user.role = 'landlord'
            user.save()

            if not hasattr(user, 'landlord_profile'):
                Landlord.objects.create(user=user)
                print("Landlord model created.")

            messages.success(request, "Landlord registered successfully.")
            return redirect('admin_dashboard')
        else:
            print("Form not valid:", form.errors)
    else:
        form = LandlordCreationForm()

    return render(request, 'register_landlord.html', {'form': form})

@login_required
def register_resident(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST or None, role='resident')
        if form.is_valid():
            user = form.save()
            landlord = form.cleaned_data['landlord']
            house = form.cleaned_data['house']
            Resident.objects.create(user=user, landlord=landlord, house=house)
            messages.success(request, "Resident registered successfully.")
            return redirect('admin_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register_resident.html', {'form': form})

@login_required
def resident_list(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    residents = Resident.objects.all()
    return render(request, 'resident_list.html', {'residents': residents})

@login_required
def landlord_list(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    landlords = Landlord.objects.all()
    return render(request, 'landlord_list.html', {'landlords': landlords})

from django.core.paginator import Paginator

@login_required
def visitor_history(request):
    if request.user.is_staff:  # Admin can see all visitor history
        visitor_requests = VisitorRequest.objects.all()
    else:  # Resident can only see their own visitor history
        visitor_requests = VisitorRequest.objects.filter(resident=request.user)

    # Get search query and date filters
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Apply search filter if search query is provided
    if search_query:
        visitor_requests = visitor_requests.filter(visitor_name__icontains=search_query)

    # Apply date filters if start and end dates are provided
    if start_date:
        visitor_requests = visitor_requests.filter(created_at__gte=start_date)
    if end_date:
        visitor_requests = visitor_requests.filter(created_at__lte=end_date)

    # Pagination
    paginator = Paginator(visitor_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'visitor_history.html', {
        'page_obj': page_obj,
    })




@login_required
def get_houses(request):
    landlord_id = request.GET.get('landlord_id')
    if not landlord_id:
        return JsonResponse([], safe=False)

    houses = House.objects.filter(landlord_id=landlord_id).select_related('street').values(
        'id', 'number', 'street__name'
    )

    return JsonResponse(list(houses), safe=False)



@login_required
def landlord_dashboard(request):
    if not hasattr(request.user, 'landlord_profile'):
        raise PermissionDenied()

    houses = request.user.landlord_profile.houses.all()
    tenants = Resident.objects.filter(landlord=request.user.landlord_profile)

    return render(request, 'landlord_dashboard.html', {
        'houses': houses,
        'tenants': tenants
    })


@login_required 
def raise_visitor_request(request):
    if request.method == 'POST':
        form = VisitorRequestForm(request.POST, user=request.user)
        if form.is_valid():
            visitor_request = form.save(commit=False)
            visitor_request.raised_by = request.user.role

            # Resident raising the request
            if request.user.role == 'resident':
                visitor_request.resident = request.user  # ✅ set resident explicitly here
                visitor_request.status = 'approved'
                visitor_request.resident_approved = True
                visitor_request.unique_code = generate_unique_code()
                visitor_request.expires_at = timezone.now() + timedelta(hours=2)
                visitor_request.save()

                # Notify security via WebSocket
                async_to_sync(channel_layer.group_send)(
                    "estate_notifications",
                    {
                        "type": "send_notification",
                        "message": f"New visitor approved by {visitor_request.resident.username}. Code: {visitor_request.unique_code}"
                    }
                )

                messages.success(request, f"Visitor request raised and auto-approved. Code: {visitor_request.unique_code}")

            # Admin or Security raising the request
            else:
                visitor_request.status = 'pending'
                visitor_request.resident_approved = False
                visitor_request.save()

                # Notify resident via WebSocket
                async_to_sync(channel_layer.group_send)(
                    "estate_notifications",
                    {
                        "type": "send_notification",
                        "message": f"New visitor request for {visitor_request.resident.username} awaiting approval."
                    }
                )

                messages.success(request, "Visitor request submitted and awaiting resident approval.")

            return redirect('dashboard')

    else:
        form = VisitorRequestForm(user=request.user)

    return render(request, 'raise_visitor_request.html', {'form': form})
    

@login_required
def approve_visitor_request(request, pk):
    visitor_request = get_object_or_404(VisitorRequest, pk=pk)

    # Only resident assigned to the request can approve
    if request.user != visitor_request.resident:
        return HttpResponseForbidden("You don't have permission to approve this request.")

    visitor_request.status = 'approved'
    visitor_request.unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    visitor_request.save()

    # Send SMS upon approval
    if visitor_request.phone_number:
        sms_message = (
            f"Hello {visitor_request.visitor_name}, your visit code is: {visitor_request.unique_code}. "
            f"Expires: {visitor_request.expires_at.strftime('%Y-%m-%d %H:%M')}"
        )
        success, response = send_sms(visitor_request.phone_number, sms_message)
        if not success:
            print(f"SMS failed: {response}")

    return redirect('dashboard_url')



@login_required
def approve_visitor(request, visitor_id):
    visitor_request = get_object_or_404(VisitorRequest, id=visitor_id)

    # Ensure that the current user is the resident of the visitor request
    if request.user != visitor_request.resident:
        raise PermissionDenied()

    # Generate a unique code for the visitor request
    visitor_request.unique_code = generate_unique_code()

    # Update the status to 'approved'
    visitor_request.status = 'approved'
    visitor_request.save()

    # Notify the security guard about the approval
    async_to_sync(channel_layer.group_send)(
        "estate_notifications",
        {
            "type": "send_notification",
            "message": f"Visitor for {visitor_request.resident.username} has been approved."
        }
    )
    
    messages.success(request, 'Visitor approved and code generated.')
    return redirect('resident_dashboard')



@login_required
def reject_visitor(request, visitor_id):
    visitor_request = get_object_or_404(VisitorRequest, id=visitor_id)

    # Ensure that the current user is the resident of the visitor request
    if request.user != visitor_request.resident:
        raise PermissionDenied()  # Prevent unauthorized users from rejecting

    # Update the status to 'rejected'
    visitor_request.status = 'rejected'
    visitor_request.resident_approved = False  # Indicate the resident did not approve
    visitor_request.save()

    # Notify the security guard about the rejection
    async_to_sync(channel_layer.group_send)(
        "estate_notifications",
        {
            "type": "send_notification",
            "message": f"Visitor for {visitor_request.resident.username} has been rejected."
        }
    )
    
    messages.success(request, 'Visitor rejected.')
    return redirect('resident_dashboard')

@login_required
def visitor_check_in(request):
    if request.method == 'POST':
        code = request.POST.get('unique_code')
        try:
            visitor_request = VisitorRequest.objects.get(unique_code=code)
        except VisitorRequest.DoesNotExist:
            messages.error(request, 'Invalid visitor code.')
            return redirect('check_in_page')

        if visitor_request.status != 'approved':
            messages.error(request, 'Visitor not approved yet.')
            return redirect('check_in_page')

        if visitor_request.expires_at and timezone.now() > visitor_request.expires_at:
            messages.error(request, 'Visitor code has expired.')
            return redirect('check_in_page')

        visitor_request.status = 'checked_in'
        visitor_request.save()

        async_to_sync(channel_layer.group_send)(
            "estate_notifications",
            {
                "type": "send_notification",
                "message": f"{visitor_request.visitor_name} has checked in at the estate gate."
            }
        )

        messages.success(request, f"Visitor {visitor_request.visitor_name} checked in successfully.")
        return redirect('check_in_page')

    return render(request, 'visitor_check_in.html')



@login_required
def visitor_check_out(request):
    if request.method == 'POST':
        code = request.POST.get('unique_code')
        try:
            visitor_request = VisitorRequest.objects.get(unique_code=code)
        except VisitorRequest.DoesNotExist:
            messages.error(request, 'Invalid visitor code.')
            return redirect('check_out_page')

        if visitor_request.status != 'checked_in':
            messages.error(request, 'Visitor is not currently checked in.')
            return redirect('check_out_page')

        visitor_request.status = 'checked_out'
        visitor_request.save()

        async_to_sync(channel_layer.group_send)(
            "estate_notifications",
            {
                "type": "send_notification",
                "message": f"{visitor_request.visitor_name} has checked out of the estate."
            }
        )

        messages.success(request, f"Visitor {visitor_request.visitor_name} checked out successfully.")
        return redirect('check_out_page')

    return render(request, 'visitor_check_out.html')


@login_required
def resident_dashboard(request):
    # Fetch all visitor requests for the logged-in resident
    visitor_requests = VisitorRequest.objects.filter(resident=request.user).order_by('-created_at')

    # Filter based on different statuses for easy access in the dashboard
    pending_requests = visitor_requests.filter(status='pending')
    approved_requests = visitor_requests.filter(status='approved')
    checked_in_requests = visitor_requests.filter(status='checked_in')
    checked_out_requests = visitor_requests.filter(status='checked_out')

    context = {
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'checked_in_requests': checked_in_requests,
        'checked_out_requests': checked_out_requests,
    }
    return render(request, 'resident_dashboard.html', context)



@login_required
def verify_visitor_code(request):
    result = None
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            visitor = VisitorRequest.objects.get(unique_code=code)
            if visitor.status != 'approved':
                message = 'Visitor is not approved yet.'
            elif visitor.expires_at and timezone.now() > visitor.expires_at:
                message = 'Code has expired.'
            else:
                # Visitor is approved and code is valid
                visitor.status = 'checked_in'
                visitor.save()

                # Notify the resident that their visitor has been checked in
                async_to_sync(channel_layer.group_send)(
                    f"estate_notifications_{visitor.resident.id}",
                    {
                        "type": "send_notification",
                        "message": f"Visitor {visitor.visitor_name} has been checked in."
                    }
                )
                
                result = {'valid': True, 'visitor': visitor}
                return render(request, 'verify_visitor_code.html', {'result': result})

        except VisitorRequest.DoesNotExist:
            result = {'valid': False, 'message': 'Invalid code entered.'}

    return render(request, 'verify_visitor_code.html', {'result': result})


@login_required
def checkin_visitor(request, visitor_id):
    if not (request.user.is_staff or request.user.is_security_guard):
        raise PermissionDenied()

    visitor_request = get_object_or_404(VisitorRequest, pk=visitor_id)

    if visitor_request.status != 'approved':
        messages.error(request, 'Visitor can only be checked in if approved.')
        return redirect(request.META.get('HTTP_REFERER', 'security_dashboard'))

    visitor_request.status = 'checked_in'
    visitor_request.save()

    messages.success(request, f'Visitor {visitor_request.visitor_name} checked in successfully.')

    # Redirect back to where they came from
    return redirect(request.META.get('HTTP_REFERER', 'security_dashboard'))


@login_required
def checkout_visitor(request, visitor_id):
    if not (request.user.is_staff or request.user.is_security_guard):
        raise PermissionDenied()  # Prevent unauthorized access

    visitor_request = get_object_or_404(VisitorRequest, id=visitor_id)

    # Only allow checkout if already checked in or approved
    if visitor_request.status in ['approved', 'checked_in']:
        visitor_request.status = 'checked_out'
        visitor_request.save()
        messages.success(request, f'Visitor {visitor_request.visitor_name} checked out successfully.')
    else:
        messages.error(request, 'Cannot check out a visitor who has not been approved or already checked in.')

    return redirect('admin_dashboard' if request.user.is_staff else 'security_dashboard')


@login_required
def make_payment(request):
    current_dues = Dues.objects.filter(is_active=True).first()
    current_year = timezone.now().year

    if not current_dues:
        # Skip calculations — show empty form and notice in template
        return render(request, 'make_payment.html', {
            'current_dues': None,
            'annual_due': None,
            'balance_due': None,
            'form': None
        })

    # Calculate total amount due for the year
    if request.user.role == 'resident':
        annual_due = current_dues.resident_due * 12
    elif request.user.role == 'landlord':
        annual_due = current_dues.landlord_due * 12
    else:
        messages.error(request, "You are not authorized to make dues payments.")
        return redirect('dashboard')

    total_paid = Payment.objects.filter(
        user=request.user, 
        status='approved', 
        year=current_year
    ).aggregate(total=models.Sum('amount'))['total'] or 0

    balance_due = annual_due - total_paid

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            months_paid_for = form.cleaned_data['months_paid_for']
            receipt = form.cleaned_data['receipt']

            if request.user.role == 'resident':
                amount_to_pay = current_dues.resident_due * months_paid_for
            elif request.user.role == 'landlord':
                amount_to_pay = current_dues.landlord_due * months_paid_for

            payment = form.save(commit=False)
            payment.user = request.user
            payment.amount = amount_to_pay
            payment.due = current_dues
            payment.status = 'pending'
            payment.year = current_year
            payment.save()

            messages.success(request, f"Payment of ₦{amount_to_pay} for {months_paid_for} month(s) submitted, awaiting approval.")
            return redirect('payment_history')
        else:
            messages.error(request, "There was an issue with your payment submission.")
    else:
        form = PaymentForm()

    return render(request, 'make_payment.html', {
        'current_dues': current_dues,
        'annual_due': annual_due,
        'balance_due': balance_due,
        'form': form
    })


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
    current_dues = Dues.objects.filter(is_active=True).first()

    # Group payments by year
    payments_by_year = defaultdict(list)
    for payment in payments:
        year = payment.payment_date.year
        payments_by_year[year].append(payment)

    # Calculate per year summary
    yearly_summary = {}
    for year, year_payments in payments_by_year.items():
        total_paid = sum(p.amount for p in year_payments if p.status == 'approved')
        if request.user.role == 'resident':
            annual_due = current_dues.resident_due * 12
        elif request.user.role == 'landlord':
            annual_due = current_dues.landlord_due * 12
        else:
            annual_due = 0

        balance = annual_due - total_paid
        yearly_summary[year] = {
            'total_paid': total_paid,
            'annual_due': annual_due,
            'balance': balance,
            'payments': year_payments,
        }

    # Paginate yearly payments
    paginator = Paginator(list(yearly_summary.items()), 1)  # Show 1 year summary per page (adjust as needed)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'payment_history.html', {
        'yearly_summary': page_obj
    })

@login_required
def set_dues(request):
    if not request.user.is_staff:
        raise PermissionDenied()
    
    current_dues = Dues.objects.first()  # Get the first dues record (or None)

    if request.method == 'POST':
        form = DuesForm(request.POST, instance=current_dues)
        if form.is_valid():
            form.save()
            messages.success(request, "Dues have been updated successfully.")
            return redirect('set_dues')  # Redirect to this page after success
    else:
        form = DuesForm(instance=current_dues)

    return render(request, 'set_dues.html', {'form': form, 'current_dues': current_dues})


@login_required
def add_dependent(request):
    if request.method == 'POST':
        form = DependentForm(request.POST)
        if form.is_valid():
            dependent = form.save(commit=False)
            dependent.resident = request.user.resident_profile  # Corrected line
            dependent.save()
            messages.success(request, f"Dependent {dependent.name} added successfully.")
            return redirect('resident_dependents')
    else:
        form = DependentForm()

    return render(request, 'add_dependent.html', {'form': form})


@login_required
def resident_dependents(request):
    resident = request.user.resident_profile
    dependents = resident.dependents.all()
    if request.method == 'POST':
        form = DependentForm(request.POST)
        if form.is_valid():
            dependent = form.save(commit=False)
            dependent.resident = resident
            dependent.save()
            return redirect('resident_dependents')
    else:
        form = DependentForm()
    return render(request, 'resident_dependents.html', {'dependents': dependents, 'form': form})

@login_required
def admin_residents_and_dependents(request):
    query = request.GET.get('q')
    if query:
        residents = Resident.objects.filter(
            unique_code__icontains=query
        ).prefetch_related('dependents')
    else:
        residents = Resident.objects.all().prefetch_related('dependents')

    return render(request, 'admin_resident_dependents.html', {'residents': residents})

class view_dependent(ListView):
    model = Dependent
    template_name = 'dependent_list.html'
    context_object_name = 'dependents'

    def get_queryset(self):
        # Display only dependents associated with the current user (resident/admin)
        if self.request.user.is_staff:  # Admin
            return Dependent.objects.all()
        else:  # Resident, show only their dependents
            resident = Resident.objects.get(user=self.request.user)
            return Dependent.objects.filter(resident=resident)