from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from FutureStarAPI.models import *
from FutureStarGameSystem.models import OfficialsType
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from FutureStarAPI.models import MobileDashboardBanner,PlayingPosition
from FutureStarTournamentApp.models import TournamentGames
from FutureStarFriendlyGame.models import FriendlyGame


class LoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Phone", "class": "form-control"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "form-control"}
        )
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError('Phone is required')
        return phone


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Username", "class": "form-control"}
        )
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email", "class": "form-control"})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "form-control"}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password check", "class": "form-control"}
        )
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


# User Category Form
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name_en", "name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter category name"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل اسم الفئة"}),

        }


# Role Form
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name_en","name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter role name"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "باسم أدخل لفة"}),

        }

# Role Form
class AgeGroupForm(forms.ModelForm):
    class Meta:
        model = AgeGroup
        fields = ["name_en","name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Age Group "}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل الفئة العمرية"}),
        }

class InjuryTypeForm(forms.ModelForm):
    class Meta:
        model = InjuryType
        fields = ["name_en","name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Injury Type "}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل نوع الإصابة"}),
        }


class GameOfficialsTypeForm(forms.ModelForm):
    class Meta:
        model = OfficialsType
        fields = ["name_en", "name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Officials Type in English"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل نوع المسؤول باللغة العربية"}),
        }


class AccountDeleteReasonForm(forms.ModelForm):
    class Meta:
        model = UserDeleteReason
        fields = ["name_en", "name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Delete Reason in English"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل سبب الحذف باللغة العربية"}),
        }


class TournamentGameForm(forms.ModelForm):
    class Meta:
        model = TournamentGames
        fields = [
            # General stats
            'general_team_a_possession', 'general_team_a_interception', 
            'general_team_a_offside', 'general_team_a_corner',
            'general_team_b_possession', 'general_team_b_interception', 
            'general_team_b_offside', 'general_team_b_corner',
            # Defence stats
            'defence_team_a_possession', 'defence_team_a_interception',
            'defence_team_a_offside', 'defence_team_a_corner',
            'defence_team_b_possession', 'defence_team_b_interception',
            'defence_team_b_offside', 'defence_team_b_corner',
            # Distribution stats
            'distribution_team_a_possession', 'distribution_team_a_interception',
            'distribution_team_a_offside', 'distribution_team_a_corner',
            'distribution_team_b_possession', 'distribution_team_b_interception',
            'distribution_team_b_offside', 'distribution_team_b_corner',
            # Attack stats
            'attack_team_a_possession', 'attack_team_a_interception',
            'attack_team_a_offside', 'attack_team_a_corner',
            'attack_team_b_possession', 'attack_team_b_interception',
            'attack_team_b_offside', 'attack_team_b_corner',
            # Discipline stats
            'discipline_team_a_possession', 'discipline_team_a_interception',
            'discipline_team_a_offside', 'discipline_team_a_corner',
            'discipline_team_b_possession', 'discipline_team_b_interception',
            'discipline_team_b_offside', 'discipline_team_b_corner',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        if instance:
            team_a_name = instance.team_a.team_name if instance.team_a else "Team A"
            team_b_name = instance.team_b.team_name if instance.team_b else "Team B"

            # Update labels for team A stats
            self.fields['general_team_a_possession'].label = f"{team_a_name} General Possession"
            self.fields['general_team_a_interception'].label = f"{team_a_name} General Interceptions"
            self.fields['general_team_a_offside'].label = f"{team_a_name} General Offsides"
            self.fields['general_team_a_corner'].label = f"{team_a_name} General Corners"

            self.fields['defence_team_a_possession'].label = f"{team_a_name} Defence Possession"
            self.fields['defence_team_a_interception'].label = f"{team_a_name} Defence Interceptions"
            self.fields['defence_team_a_offside'].label = f"{team_a_name} Defence Offsides"
            self.fields['defence_team_a_corner'].label = f"{team_a_name} Defence Corners"

            self.fields['distribution_team_a_possession'].label = f"{team_a_name} Distribution Possession"
            self.fields['distribution_team_a_interception'].label = f"{team_a_name} Distribution Interceptions"
            self.fields['distribution_team_a_offside'].label = f"{team_a_name} Distribution Offsides"
            self.fields['distribution_team_a_corner'].label = f"{team_a_name} Distribution Corners"

            self.fields['attack_team_a_possession'].label = f"{team_a_name} Attack Possession"
            self.fields['attack_team_a_interception'].label = f"{team_a_name} Attack Interceptions"
            self.fields['attack_team_a_offside'].label = f"{team_a_name} Attack Offsides"
            self.fields['attack_team_a_corner'].label = f"{team_a_name} Attack Corners"

            self.fields['discipline_team_a_possession'].label = f"{team_a_name} Discipline Possession"
            self.fields['discipline_team_a_interception'].label = f"{team_a_name} Discipline Interceptions"
            self.fields['discipline_team_a_offside'].label = f"{team_a_name} Discipline Offsides"
            self.fields['discipline_team_a_corner'].label = f"{team_a_name} Discipline Corners"

            # Update labels for team B stats
            self.fields['general_team_b_possession'].label = f"{team_b_name} General Possession"
            self.fields['general_team_b_interception'].label = f"{team_b_name} General Interceptions"
            self.fields['general_team_b_offside'].label = f"{team_b_name} General Offsides"
            self.fields['general_team_b_corner'].label = f"{team_b_name} General Corners"

            self.fields['defence_team_b_possession'].label = f"{team_b_name} Defence Possession"
            self.fields['defence_team_b_interception'].label = f"{team_b_name} Defence Interceptions"
            self.fields['defence_team_b_offside'].label = f"{team_b_name} Defence Offsides"
            self.fields['defence_team_b_corner'].label = f"{team_b_name} Defence Corners"

            self.fields['distribution_team_b_possession'].label = f"{team_b_name} Distribution Possession"
            self.fields['distribution_team_b_interception'].label = f"{team_b_name} Distribution Interceptions"
            self.fields['distribution_team_b_offside'].label = f"{team_b_name} Distribution Offsides"
            self.fields['distribution_team_b_corner'].label = f"{team_b_name} Distribution Corners"

            self.fields['attack_team_b_possession'].label = f"{team_b_name} Attack Possession"
            self.fields['attack_team_b_interception'].label = f"{team_b_name} Attack Interceptions"
            self.fields['attack_team_b_offside'].label = f"{team_b_name} Attack Offsides"
            self.fields['attack_team_b_corner'].label = f"{team_b_name} Attack Corners"

            self.fields['discipline_team_b_possession'].label = f"{team_b_name} Discipline Possession"
            self.fields['discipline_team_b_interception'].label = f"{team_b_name} Discipline Interceptions"
            self.fields['discipline_team_b_offside'].label = f"{team_b_name} Discipline Offsides"
            self.fields['discipline_team_b_corner'].label = f"{team_b_name} Discipline Corners"


class FriendlyGameForm(forms.ModelForm):
    class Meta:
        model = FriendlyGame
        fields = [
            # General stats
            'general_team_a_possession', 'general_team_a_interception', 
            'general_team_a_offside', 'general_team_a_corner',
            'general_team_b_possession', 'general_team_b_interception', 
            'general_team_b_offside', 'general_team_b_corner',
            # Defence stats
            'defence_team_a_possession', 'defence_team_a_interception',
            'defence_team_a_offside', 'defence_team_a_corner',
            'defence_team_b_possession', 'defence_team_b_interception',
            'defence_team_b_offside', 'defence_team_b_corner',
            # Distribution stats
            'distribution_team_a_possession', 'distribution_team_a_interception',
            'distribution_team_a_offside', 'distribution_team_a_corner',
            'distribution_team_b_possession', 'distribution_team_b_interception',
            'distribution_team_b_offside', 'distribution_team_b_corner',
            # Attack stats
            'attack_team_a_possession', 'attack_team_a_interception',
            'attack_team_a_offside', 'attack_team_a_corner',
            'attack_team_b_possession', 'attack_team_b_interception',
            'attack_team_b_offside', 'attack_team_b_corner',
            # Discipline stats
            'discipline_team_a_possession', 'discipline_team_a_interception',
            'discipline_team_a_offside', 'discipline_team_a_corner',
            'discipline_team_b_possession', 'discipline_team_b_interception',
            'discipline_team_b_offside', 'discipline_team_b_corner',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        if instance:
            team_a_name = instance.team_a.team_name if instance.team_a else "Team A"
            team_b_name = instance.team_b.team_name if instance.team_b else "Team B"

            # Update labels for team A stats
            self.fields['general_team_a_possession'].label = f"{team_a_name} General Possession"
            self.fields['general_team_a_interception'].label = f"{team_a_name} General Interceptions"
            self.fields['general_team_a_offside'].label = f"{team_a_name} General Offsides"
            self.fields['general_team_a_corner'].label = f"{team_a_name} General Corners"

            self.fields['defence_team_a_possession'].label = f"{team_a_name} Defence Possession"
            self.fields['defence_team_a_interception'].label = f"{team_a_name} Defence Interceptions"
            self.fields['defence_team_a_offside'].label = f"{team_a_name} Defence Offsides"
            self.fields['defence_team_a_corner'].label = f"{team_a_name} Defence Corners"

            self.fields['distribution_team_a_possession'].label = f"{team_a_name} Distribution Possession"
            self.fields['distribution_team_a_interception'].label = f"{team_a_name} Distribution Interceptions"
            self.fields['distribution_team_a_offside'].label = f"{team_a_name} Distribution Offsides"
            self.fields['distribution_team_a_corner'].label = f"{team_a_name} Distribution Corners"

            self.fields['attack_team_a_possession'].label = f"{team_a_name} Attack Possession"
            self.fields['attack_team_a_interception'].label = f"{team_a_name} Attack Interceptions"
            self.fields['attack_team_a_offside'].label = f"{team_a_name} Attack Offsides"
            self.fields['attack_team_a_corner'].label = f"{team_a_name} Attack Corners"

            self.fields['discipline_team_a_possession'].label = f"{team_a_name} Discipline Possession"
            self.fields['discipline_team_a_interception'].label = f"{team_a_name} Discipline Interceptions"
            self.fields['discipline_team_a_offside'].label = f"{team_a_name} Discipline Offsides"
            self.fields['discipline_team_a_corner'].label = f"{team_a_name} Discipline Corners"

            # Update labels for team B stats
            self.fields['general_team_b_possession'].label = f"{team_b_name} General Possession"
            self.fields['general_team_b_interception'].label = f"{team_b_name} General Interceptions"
            self.fields['general_team_b_offside'].label = f"{team_b_name} General Offsides"
            self.fields['general_team_b_corner'].label = f"{team_b_name} General Corners"

            self.fields['defence_team_b_possession'].label = f"{team_b_name} Defence Possession"
            self.fields['defence_team_b_interception'].label = f"{team_b_name} Defence Interceptions"
            self.fields['defence_team_b_offside'].label = f"{team_b_name} Defence Offsides"
            self.fields['defence_team_b_corner'].label = f"{team_b_name} Defence Corners"

            self.fields['distribution_team_b_possession'].label = f"{team_b_name} Distribution Possession"
            self.fields['distribution_team_b_interception'].label = f"{team_b_name} Distribution Interceptions"
            self.fields['distribution_team_b_offside'].label = f"{team_b_name} Distribution Offsides"
            self.fields['distribution_team_b_corner'].label = f"{team_b_name} Distribution Corners"

            self.fields['attack_team_b_possession'].label = f"{team_b_name} Attack Possession"
            self.fields['attack_team_b_interception'].label = f"{team_b_name} Attack Interceptions"
            self.fields['attack_team_b_offside'].label = f"{team_b_name} Attack Offsides"
            self.fields['attack_team_b_corner'].label = f"{team_b_name} Attack Corners"

            self.fields['discipline_team_b_possession'].label = f"{team_b_name} Discipline Possession"
            self.fields['discipline_team_b_interception'].label = f"{team_b_name} Discipline Interceptions"
            self.fields['discipline_team_b_offside'].label = f"{team_b_name} Discipline Offsides"
            self.fields['discipline_team_b_corner'].label = f"{team_b_name} Discipline Corners"

# Field Capacity Form
class FieldCapacityForm(forms.ModelForm):
    class Meta:
        model = FieldCapacity
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter Field Capacity"}),
        }


# Slider Content Form
class Slider_ContentForm(forms.ModelForm):
    class Meta:
        model = Slider_Content
        fields = ["content_en","content_ar"]
        widgets = {
            "content_en": forms.TextInput(attrs={"placeholder": "Enter content"}),
            "content_ar": forms.TextInput(attrs={"placeholder": "Enter content"}),

        }


# Ground Material Form
class GroundMaterialForm(forms.ModelForm):
    class Meta:
        model = GroundMaterial
        fields = ["name_en","name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Ground Material"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل المواد الأرضية"}),

        }


# Event Type Style Form
class EventTypeForm(forms.ModelForm):
    class Meta:
        model = EventType
        fields = ["name_en","name_ar"]
        widgets = {
            "name_en": forms.TextInput(attrs={"placeholder": "Enter Event Type"}),
            "name_ar": forms.TextInput(attrs={"placeholder": "أدخل نوع الحدث"}),

        }


class UserUpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "phone",
            "profile_picture",
            "card_header",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set common attributes for all fields
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
            field.required = False

        # Make specific fields read-only
        readonly_fields = ["username", "email", "phone"]
        for field_name in readonly_fields:
            self.fields[field_name].widget.attrs["readonly"] = True


class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        return new_password2



class MobileDashboardBannerForm(forms.ModelForm):
    class Meta:
        model = MobileDashboardBanner
        fields = ['id','image']


class PlayingPositionForm(forms.ModelForm):
    class Meta:
        model = PlayingPosition
        fields = ["name_en","name_ar","shortname"]