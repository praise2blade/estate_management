from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Landlord, House, Resident, VisitorRequest, Street, Payment, Dues, Dependent
from django.utils import timezone
from datetime import timedelta


class VisitorRequestForm(forms.ModelForm):
    class Meta:
        model = VisitorRequest
        fields = ['visitor_name', 'purpose', 'phone_number', 'resident', 'expires_at']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['expires_at'].initial = timezone.now() + timedelta(hours=2)

        if user:
            if user.role == 'resident':
                self.fields['resident'].required = False  # 👈 this line is important
                self.fields['resident'].widget = forms.HiddenInput()
            elif user.role == 'admin':
                self.fields['resident'].queryset = User.objects.filter(role='resident')



class CustomUserCreationForm(UserCreationForm):
    landlord = forms.ModelChoiceField(queryset=Landlord.objects.all(), empty_label="Select a Landlord", required=False)
    house = forms.ModelChoiceField(queryset=House.objects.none(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        self.role = kwargs.pop('role', None)  # get role from kwargs
        super().__init__(*args, **kwargs)

        self.fields['landlord'].widget.attrs.update({'id': 'id_landlord'})
        self.fields['house'].widget.attrs.update({'id': 'id_house'})

        if 'landlord' in self.data:
            try:
                landlord_id = int(self.data.get('landlord'))
                self.fields['house'].queryset = House.objects.filter(landlord_id=landlord_id)
            except (ValueError, TypeError):
                self.fields['house'].queryset = House.objects.none()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.role  # assign role passed from view
        if commit:
            user.save()
        return user


class LandlordCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['number', 'street', 'landlord']

class StreetForm(forms.ModelForm):
    class Meta:
        model = Street
        fields = ['name', 'city', 'state']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['months_paid_for', 'receipt']

    months_paid_for = forms.IntegerField(min_value=1, required=True)
    receipt = forms.FileField(required=True)


class DuesForm(forms.ModelForm):
    class Meta:
        model = Dues
        fields = ['resident_due', 'landlord_due', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resident_due'].widget.attrs.update({'class': 'form-input'})
        self.fields['landlord_due'].widget.attrs.update({'class': 'form-input'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-checkbox'})


class DependentForm(forms.ModelForm):
    class Meta:
        model = Dependent
        fields = ['name', 'dependent_type', 'relationship']
        widgets = {
            'dependent_type': forms.Select(attrs={
                'class': 'block w-full mt-1 rounded-md border-gray-300'
            }),
            'name': forms.TextInput(attrs={
                'class': 'block w-full mt-1 rounded-md border-gray-300'
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'block w-full mt-1 rounded-md border-gray-300'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If you want any custom validation or adjustments, you can add them here
