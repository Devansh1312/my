from django import forms
from FutureStarAPI.models import OTPSave  # Adjust this to your model path
from FutureStar_App.models import User
# class RegistrationForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput())
#     confirm_password = forms.CharField(widget=forms.PasswordInput())

#     class Meta:
#         model = OTPSave
#         fields = ['username', 'phone', 'password', 'confirm_password']

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get('password')
#         confirm_password = cleaned_data.get('confirm_password')

#         if password != confirm_password:
#             raise forms.ValidationError("Passwords do not match.")


class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True)

class UserInfoForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)  # For password input

    class Meta:
        model = User
        fields = ['email', 'username', 'phone', 'password']
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),  # Make email readonly
        }