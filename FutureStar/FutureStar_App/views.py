import os
from django.shortcuts import render, redirect, get_object_or_404
from django import views
from .forms import *
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SystemSettings
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# Login Module
def LoginFormView(request):
    # If the user is already logged in, redirect to the dashboard
    if request.user.is_authenticated:
        return redirect("Dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        remember_me = request.POST.get("rememberMe") == "on"
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(
                request, email=email, password=password
            )  

            if user is not None:
                if user.is_active:  # Check if the user is active
                    if user.role_id == 1:  # Check if user's role_id is 1
                        login(request, user)
                        if remember_me:
                            request.session.set_expiry(1209600)
                        messages.success(request, "Login Successful")
                        return redirect("Dashboard")
                    else:
                        messages.error(
                            request,
                            "You do not have the required role to access this site.",
                        )
                else:
                    # Add error message if user account is deactivated
                    messages.error(
                        request,
                        "Your account is deactivated. Please contact the admin.",
                    )
            else:
                # Add error message for invalid credentials
                messages.error(request, "Invalid email or password")
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "AdminLogin.html", {"form": form})


# Forgot Password Module
class ForgotPasswordView(View):
    template_name = "Admin/Auth/forgot_password.html"
    User = get_user_model()

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email")
        user = self.User.objects.filter(email=email).first()

        if user:
            user.remember_token = get_random_string(40)
            user.token_created_at = timezone.now()
            user.save()
            reset_url = request.build_absolute_uri(
                reverse("reset_password", args=[user.remember_token])
            )

            context = {"user": user, "reset_url": reset_url}

            subject = "Reset Your Password"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            html_content = render_to_string("Admin/Email/reset_password.html", context)

            msg = EmailMultiAlternatives(subject, "", from_email, to_email)
            msg.attach_alternative(html_content, "text/html")

            try:
                msg.send()
                messages.success(request, "Please check your email for the reset link.")
            except Exception as e:
                messages.error(
                    request,
                    "There was an error sending the email. Please try again later.",
                )

            return redirect("adminlogin")
        else:
            messages.error(request, "Email not found.")

        return redirect("forgot_password")


# Reset Password Module
class ResetPasswordView(View):
    template_name = "Admin/Auth/reset_password.html"
    User = get_user_model()

    def get(self, request, token):
        user = get_object_or_404(User, remember_token=token)

        # Check if the token has expired (1 hour expiration)
        expiration_time = timezone.now() - timedelta(hours=1)
        if user.token_created_at and user.token_created_at < expiration_time:
            messages.error(request, "This reset link has expired.")
            return redirect("forgot_password")

        return render(request, self.template_name, {"token": token})

    def post(self, request, token):
        user = get_object_or_404(User, remember_token=token)

        # Check if the token has expired (1 hour expiration)
        expiration_time = timezone.now() - timedelta(hours=1)
        if user.token_created_at and user.token_created_at < expiration_time:
            messages.error(request, "This reset link has expired.")
            return redirect("forgot_password")

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password == confirm_password:
            user.set_password(password)
            if not user.email_verified_at:
                user.email_verified_at = timezone.now()
            user.remember_token = get_random_string(40)  # Invalidate the token
            user.token_created_at = None  # Clear the token creation time
            user.save()
            messages.success(
                request, "Your password has been reset. You can now log in."
            )
            return redirect("adminlogin")
        else:
            messages.error(request, "Passwords do not match.")

        return render(request, self.template_name, {"token": token})


# Dashboard View
class Dashboard(LoginRequiredMixin, View):
    login_url = "/"
    redirect_field_name = "redirect_to"

    def get(self, request, *args, **kwargs):
        context = {"breadcrumb": {"parent": "Admin", "child": "Dashboard"}}
        return render(request, "Admin/Dashboard.html", context)


# Logout Module
def logout_view(request):
    logout(request)
    return redirect("adminlogin")


##################################################### User Profile View ###############################################################
class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = {
            "user": user,
            "breadcrumb": {"parent": "Acccount", "child": "Profile"},
        }

        return render(request, "Admin/User/user_profile.html", context)

    def post(self, request):
        user = request.user

        return render(request, "Admin/User/user_profile.html", {"user": user})


@method_decorator(login_required, name="dispatch")
class UserUpdateProfileView(View):
    def get(self, request, *args, **kwargs):
        form = UserUpdateProfileForm(instance=request.user)
        password_change_form = CustomPasswordChangeForm(user=request.user)
        return render(
            request,
            "Admin/User/edit_profile.html",
            {
                "form": form,
                "password_change_form": password_change_form,
                "breadcrumb": {"parent": "Acccount", "child": "Edit Profile"},
            },
        )

    def post(self, request, *args, **kwargs):
        if "change_password" in request.POST:
            # Handle password change
            password_change_form = CustomPasswordChangeForm(
                user=request.user, data=request.POST
            )
            if password_change_form.is_valid():
                user = password_change_form.save()
                logout(request)  # Log out the user after password change
                messages.success(
                    request,
                    "Your password has been changed successfully. Please log in again.",
                )
                return redirect("adminlogin")
            else:
                form = UserUpdateProfileForm(instance=request.user)
                # Render the same template with the form errors
                return render(
                    request,
                    "Admin/Dashboard.html",
                    {
                        "form": form,
                        "password_change_form": password_change_form,
                        "show_change_password_modal": True,
                    },
                )
        else:
            # Handle profile update
            user = request.user
            old_profile_picture = user.profile_picture
            old_card_header = user.card_header

            form = UserUpdateProfileForm(
                request.POST, instance=user, files=request.FILES
            )
            if form.is_valid():
                # Handle profile picture update
                if "profile_picture" in request.FILES:
                    if old_profile_picture and os.path.isfile(
                        os.path.join(settings.MEDIA_ROOT, str(old_profile_picture))
                    ):
                        os.remove(
                            os.path.join(settings.MEDIA_ROOT, str(old_profile_picture))
                        )
                elif "profile_picture-clear" in request.POST:
                    user.profile_picture = None

                # Handle card header update
                if "card_header" in request.FILES:
                    if old_card_header and os.path.isfile(
                        os.path.join(settings.MEDIA_ROOT, str(old_card_header))
                    ):
                        os.remove(
                            os.path.join(settings.MEDIA_ROOT, str(old_card_header))
                        )
                elif "card_header-clear" in request.POST:
                    user.card_header = None

                user = form.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect("edit_profile")
            else:
                for field in form:
                    for error in field.errors:
                        messages.error(request, error)
                password_change_form = CustomPasswordChangeForm(user=request.user)
                return render(
                    request,
                    "Admin/User/edit_profile.html",
                    {"form": form, "password_change_form": password_change_form},
                )


################################## SytemSettings view #######################################################
class System_Settings(LoginRequiredMixin, View):
    login_url = "/"
    redirect_field_name = "redirect_to"

    def get(self, request, *args, **kwargs):
        system_settings = SystemSettings.objects.first()  # Fetch the first record
        return render(
            request,
            "Admin/System_Settings.html",
            {
                "system_settings": system_settings,
                "MEDIA_URL": settings.MEDIA_URL,
                "breadcrumb": {
                    "parent": "Admin",
                    "child": "System Settings",
                },  # Pass MEDIA_URL to the template
            },
        )

    def post(self, request, *args, **kwargs):
        system_settings = SystemSettings.objects.first()
        if not system_settings:
            system_settings = SystemSettings()

        fs = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, "System_Settings")
        )

        errors = {}
        success = False

        try:
            # Handle fav_icon
            if "fav_icon" in request.FILES:
                if system_settings.fav_icon:
                    old_fav_icon_path = os.path.join(
                        settings.MEDIA_ROOT, system_settings.fav_icon
                    )
                    if os.path.isfile(old_fav_icon_path):
                        os.remove(old_fav_icon_path)
                fav_icon_file = request.FILES["fav_icon"]
                fav_icon_filename = "favicon.jpg"
                fs.save(fav_icon_filename, fav_icon_file)
                system_settings.fav_icon = os.path.join(
                    "System_Settings", fav_icon_filename
                )

            # Handle footer_logo
            if "footer_logo" in request.FILES:
                if system_settings.footer_logo:
                    old_footer_logo_path = os.path.join(
                        settings.MEDIA_ROOT, system_settings.footer_logo
                    )
                    if os.path.isfile(old_footer_logo_path):
                        os.remove(old_footer_logo_path)
                footer_logo_file = request.FILES["footer_logo"]
                footer_logo_filename = "footer_logo.jpg"
                fs.save(footer_logo_filename, footer_logo_file)
                system_settings.footer_logo = os.path.join(
                    "System_Settings", footer_logo_filename
                )

            # Handle header_logo
            if "header_logo" in request.FILES:
                if system_settings.header_logo:
                    old_header_logo_path = os.path.join(
                        settings.MEDIA_ROOT, system_settings.header_logo
                    )
                    if os.path.isfile(old_header_logo_path):
                        os.remove(old_header_logo_path)
                header_logo_file = request.FILES["header_logo"]
                header_logo_filename = "header_logo.jpg"
                fs.save(header_logo_filename, header_logo_file)
                system_settings.header_logo = os.path.join(
                    "System_Settings", header_logo_filename
                )

            # Validate and save other fields
            system_settings.website_name_english = request.POST.get(
                "website_name_english"
            )
            system_settings.website_name_arabic = request.POST.get(
                "website_name_arabic"
            )
            system_settings.phone = request.POST.get("phone")
            system_settings.email = request.POST.get("email")
            system_settings.address = request.POST.get("address")
            system_settings.instagram = request.POST.get("instagram")
            system_settings.facebook = request.POST.get("facebook")
            system_settings.twitter = request.POST.get("twitter")
            system_settings.linkedin = request.POST.get("linkedin")
            system_settings.pinterest = request.POST.get("pinterest")
            system_settings.happy_user = request.POST.get("happy_user")
            system_settings.line_of_code = request.POST.get("line_of_code")
            system_settings.downloads = request.POST.get("downloads")
            system_settings.app_rate = request.POST.get("app_rate")
            system_settings.years_of_experience = request.POST.get(
                "years_of_experience"
            )
            system_settings.project_completed = request.POST.get("project_completed")
            system_settings.proffesioan_team_members = request.POST.get(
                "proffesioan_team_members"
            )
            system_settings.awards_winning = request.POST.get("awards_winning")

            fields = {
                "website_name_english": "This field is required.",
                "website_name_arabic": "This field is required.",
                "phone": "This field is required.",
                "email": "This field is required.",
                "address": "This field is required.",
                "happy_user": "This field is required.",
                "line_of_code": "This field is required.",
                "downloads": "This field is required.",
                "app_rate": "This field is required.",
            }

            for field, error_message in fields.items():
                if not getattr(system_settings, field):
                    errors[field] = error_message

            # Add additional validations as needed

            if errors:
                messages.error(request, "Please correct the errors below.")
            else:
                system_settings.save()
                success = True
                messages.success(request, "System settings Updated Successfully.")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        if errors:
            return render(
                request,
                "Admin/System_Settings.html",
                {
                    "system_settings": system_settings,
                    "MEDIA_URL": settings.MEDIA_URL,
                    "breadcrumb": {
                        "parent": "Admin",
                        "child": "System Settings",
                    },
                    "errors": errors,
                },
            )
        elif success:
            return redirect("Dashboard")
        else:
            return redirect("Dashboard")


#######################################   Player Coach And Refree LIST VIEW MODULE ##############################################

# User Active & Deactive Function
class ToggleUserStatusView(View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        new_status = request.POST.get("status")
        source_page = request.POST.get(
            "source_page", "Dashboard"
        )  # Default to Dashboard if not provided

        # Check if the user is a superuser
        if user.role_id == 1:
            messages.error(request, "Superuser status cannot be changed.")
            return redirect("user_list")

        # Check if the current user is trying to deactivate their own account
        if user == request.user and new_status == "deactivate":
            messages.info(
                request, "Your account has been deactivated. Please log in again."
            )
            user.is_active = False
            user.save()
            return redirect(reverse("adminlogin"))

        # Update the user's status
        if new_status == "activate":
            user.is_active = True
            messages.success(request, f"{user.username} has been activated.")
        elif new_status == "deactivate":
            user.is_active = False
            messages.success(request, f"{user.username} has been deactivated.")

        user.save()

        # Redirect to the appropriate list based on source_page
        if source_page == "player_list":
            return redirect(reverse("player_list"))
        elif source_page == "coach_list":
            return redirect(reverse("coach_list"))
        elif source_page == "referee_list":
            return redirect(reverse("referee_list"))
        else:
            return redirect(reverse("Dashboard"))


# Player List View
class PlayerListView(LoginRequiredMixin, View):
    template_name = "Admin/User/Player_List.html"

    def get(self, request):
        User = get_user_model()  # Get the custom user model
        users = User.objects.filter(role_id=2)  # Fetch users where role_id is 2
        roles = Role.objects.filter(id=2)  # Fetch roles with id 2
        return render(
            request,
            self.template_name,
            {
                "users": users,
                "roles": roles,
                "breadcrumb": {"child": "Player List"},
            },
        )


# Coach List View
class CoachListView(LoginRequiredMixin, View):
    template_name = "Admin/User/Coach_List.html"

    def get(self, request):
        User = get_user_model()  # Get the custom user model
        users = User.objects.filter(role_id=3)  # Fetch users where role_id is 3
        roles = Role.objects.filter(id=3)  # Fetch roles with id 3
        return render(
            request,
            self.template_name,
            {
                "users": users,
                "roles": roles,
                "breadcrumb": {"child": "Coach List"},
            },
        )


# Refree List View
class RefereeListView(LoginRequiredMixin, View):
    template_name = "Admin/User/Referee_List.html"

    def get(self, request):
        User = get_user_model()  # Get the custom user model
        users = User.objects.filter(role_id=4)  # Fetch users where role_id is 2
        roles = Role.objects.filter(id=4)  # Fetch roles with id 2
        return render(
            request,
            self.template_name,
            {
                "users": users,
                "roles": roles,
                "breadcrumb": {"child": "Referee List"},
            },
        )


##############################################  User Category Type Module  ################################################
# Category CRUD Views
class CategoryCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = CategoryForm()
        return render(request, "forms/category_form.html", {"form": form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            # Check for existing category with the same name
            name = form.cleaned_data.get("name")
            if Category.objects.filter(name=name).exists():
                messages.error(request, "Category Type with this name already exists.")
                return redirect(
                    "category_list"
                )  # Redirect back to category_list with an error message
            form.save()
            messages.success(request, "Category Type Create Successfully.")
            return redirect("category_list")
        else:
            messages.error(
                request,
                "There was an error creating the category. Please ensure all fields are filled out correctly.",
            )
        return redirect("category_list")


class CategoryUpdateView(LoginRequiredMixin, View):
    template_name = "forms/category_form.html"

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryForm(instance=category)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category Type Updated Successfully.")
            return redirect("category_list")
        else:
            messages.error(
                request,
                "There was an error updating the category. Please ensure all fields are filled out correctly.",
            )
        return render(request, self.template_name, {"form": form})


class CategoryDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, "Category Type Deleted Successfully.")
        return redirect("category_list")

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, "Category Type Deleted Successfully.")
        return redirect("category_list")


class CategoryListView(LoginRequiredMixin, View):
    template_name = "Admin/Category_List.html"

    def get(self, request):
        categories = Category.objects.all()
        return render(
            request,
            self.template_name,
            {
                "categories": categories,
                "breadcrumb": {"parent": "User", "child": "Category Type"},
            },
        )


################################################################# Role CRUD Views ###################################################
class RoleCreateView(LoginRequiredMixin, View):
    template_name = "Admin/User_Role.html"

    def get(self, request):
        form = RoleForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Role Created successfully.")
            return redirect("role_list")
        messages.error(
            request,
            "There was an error creating the role. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class RoleUpdateView(LoginRequiredMixin, View):
    template_name = "Admin/User_Role.html"  # Fixed template name

    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        form = RoleForm(instance=role)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, "Role Updated Successfully.")
            return redirect("role_list")
        messages.error(
            request,
            "There was an error updating the role. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class RoleDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        role.delete()
        messages.success(request, "Role Deleted Successfully.")
        return redirect("role_list")

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        role.delete()
        messages.success(request, "Role Deleted Successfully.")
        return redirect("role_list")


class RoleListView(LoginRequiredMixin, View):
    template_name = "Admin/User_Role.html"

    def get(self, request):
        roles = Role.objects.all()
        return render(
            request,
            self.template_name,
            {"roles": roles, "breadcrumb": {"parent": "User", "child": "Role"}},
        )


##########################################  Gender CRUD Views  ###########################################
# class GenderCreateView(LoginRequiredMixin, View):
#     template_name = "forms/gender_form.html"

#     def get(self, request):
#         form = GenderForm()
#         return render(request, self.template_name, {"form": form})

#     def post(self, request):
#         form = GenderForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Gender created successfully.")
#             return redirect("gender_list")
#         messages.error(
#             request,
#             "There was an error creating the gender. Please ensure all fields are filled out correctly.",
#         )
#         return render(request, self.template_name, {"form": form})


# class GenderUpdateView(LoginRequiredMixin, View):
#     template_name = "forms/gender_form.html"

#     def get(self, request, pk):
#         gender = get_object_or_404(UserGender, pk=pk)
#         form = GenderForm(instance=gender)
#         return render(request, self.template_name, {"form": form})

#     def post(self, request, pk):
#         gender = get_object_or_404(UserGender, pk=pk)
#         form = GenderForm(request.POST, instance=gender)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Gender was successfully updated.")
#             return redirect("gender_list")
#         messages.error(
#             request,
#             "There was an error updating the gender. Please ensure all fields are filled out correctly.",
#         )
#         return render(request, self.template_name, {"form": form})


# class GenderDeleteView(LoginRequiredMixin, View):
#     def get(self, request, pk):
#         gender = get_object_or_404(UserGender, pk=pk)
#         gender.delete()
#         messages.success(request, "Gender was successfully deleted.")
#         return redirect("gender_list")

#     def post(self, request, pk):
#         gender = get_object_or_404(UserGender, pk=pk)
#         gender.delete()
#         messages.success(request, "Gender was successfully deleted.")
#         return redirect("gender_list")


# class GenderListView(LoginRequiredMixin, View):
#     template_name = "Admin/General_Settings/Gender.html"

#     def get(self, request):
#         genders = UserGender.objects.all()
#         return render(
#             request,
#             self.template_name,
#             {
#                 "genders": genders,
#                 "breadcrumb": {"parent": "General Settings", "child": "Gender"},
#             },
#         )


####################################### fieldcapacity CRUD Views  ########################################################
class FieldCapacityCreateView(LoginRequiredMixin, View):
    template_name = "forms/fieldcapacity_form.html"

    def get(self, request):
        form = FieldCapacityForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = FieldCapacityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Field Capacity Created successfully.")
            return redirect("fieldcapacity_list")
        messages.error(
            request,
            "There was an error creating the Field Capacity. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class FieldCapacityUpdateView(LoginRequiredMixin, View):
    template_name = "forms/fieldcapacity_form.html"

    def get(self, request, pk):
        fieldcapacity = get_object_or_404(FieldCapacity, pk=pk)
        form = FieldCapacityForm(instance=fieldcapacity)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        fieldcapacity = get_object_or_404(FieldCapacity, pk=pk)
        form = FieldCapacityForm(request.POST, instance=fieldcapacity)
        if form.is_valid():
            form.save()
            messages.success(request, "Field Capacity Updated Successfully.")
            return redirect("fieldcapacity_list")
        messages.error(
            request,
            "There was an error updating the game type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class FieldCapacityDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        fieldcapacity = get_object_or_404(FieldCapacity, pk=pk)
        fieldcapacity.delete()
        messages.success(request, "Field Capacity Successfully Deleted.")
        return redirect("fieldcapacity_list")

    def post(self, request, pk):
        fieldcapacity = get_object_or_404(FieldCapacity, pk=pk)
        fieldcapacity.delete()
        messages.success(request, "Field Capacity Successfully Deleted.")
        return redirect("fieldcapacity_list")


class FieldCapacityListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/FieldCapacity.html"

    def get(self, request):
        fieldcapacitys = FieldCapacity.objects.all()
        return render(
            request,
            self.template_name,
            {
                "fieldcapacitys": fieldcapacitys,
                "breadcrumb": {"parent": "General Settings", "child": "Field Capacity"},
            },
        )


####################################################### Ground Materials CRUD Views  ###########################################
class GroundMaterialCreateView(LoginRequiredMixin, View):
    template_name = "forms/groundmaterial_form.html"

    def get(self, request):
        form = GroundMaterialForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GroundMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ground Material Created Successfully.")
            return redirect("groundmaterial_list")
        messages.error(
            request,
            "There was an error creating the Ground Material. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class GroundMaterialUpdateView(LoginRequiredMixin, View):
    template_name = "forms/groundmaterial_form.html"

    def get(self, request, pk):
        groundmaterial = get_object_or_404(GroundMaterial, pk=pk)
        form = GroundMaterialForm(instance=groundmaterial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        groundmaterial = get_object_or_404(GroundMaterial, pk=pk)
        form = GroundMaterialForm(request.POST, instance=groundmaterial)
        if form.is_valid():
            form.save()
            messages.success(request, "Ground Material Updated Successfully.")
            return redirect("groundmaterial_list")
        messages.error(
            request,
            "There was an error updating the Ground Material. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class GroundMaterialDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        groundmaterial = get_object_or_404(GroundMaterial, pk=pk)
        groundmaterial.delete()
        messages.success(request, "Ground Material Successfully Deleted.")
        return redirect("groundmaterial_list")

    def post(self, request, pk):
        groundmaterial = get_object_or_404(GroundMaterial, pk=pk)
        groundmaterial.delete()
        messages.success(request, "Ground Material successfully deleted.")
        return redirect("groundmaterial_list")


class GroundMaterialListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/GroundMaterial.html"

    def get(self, request):
        groundmaterials = GroundMaterial.objects.all()
        return render(
            request,
            self.template_name,
            {
                "groundmaterials": groundmaterials,
                "breadcrumb": {
                    "parent": "General Settings",
                    "child": "Ground Material",
                },
            },
        )


######################################  Tournament Style CRUD Views  #############################################################
class TournamentStyleCreateView(LoginRequiredMixin, View):
    template_name = "forms/tournamentstyle_form.html"

    def get(self, request):
        form = TournamentStyleForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = TournamentStyleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tournament Style created successfully.")
            return redirect("tournamentstyle_list")
        messages.error(
            request,
            "There was an error creating the Tournament Style. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class TournamentStyleUpdateView(LoginRequiredMixin, View):
    template_name = "forms/tournamentstyle_form.html"

    def get(self, request, pk):
        tournamentstyle = get_object_or_404(TournamentStyle, pk=pk)
        form = TournamentStyleForm(instance=tournamentstyle)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        tournamentstyle = get_object_or_404(TournamentStyle, pk=pk)
        form = TournamentStyleForm(request.POST, instance=tournamentstyle)
        if form.is_valid():
            form.save()
            messages.success(request, "Tournament Style updated successfully.")
            return redirect("tournamentstyle_list")
        messages.error(
            request,
            "There was an error updating the Tournament Style. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class TournamentStyleDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        tournamentstyle = get_object_or_404(TournamentStyle, pk=pk)
        tournamentstyle.delete()
        messages.success(request, "Tournament Style successfully deleted.")
        return redirect("tournamentstyle_list")

    def post(self, request, pk):
        tournamentstyle = get_object_or_404(TournamentStyle, pk=pk)
        tournamentstyle.delete()
        messages.success(request, "Tournament Style successfully deleted.")
        return redirect("tournamentstyle_list")


class TournamentStyleListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/TournamentStyle.html"

    def get(self, request):
        tournamentstyles = TournamentStyle.objects.all()
        return render(
            request,
            self.template_name,
            {
                "tournamentstyles": tournamentstyles,
                "breadcrumb": {"parent": "General Settings", "child": "Tournaments"},
            },
        )


################################################### Event Type CRUD Views #######################################################
class EventTypeCreateView(LoginRequiredMixin, View):
    template_name = "forms/eventtype_form.html"

    def get(self, request):
        form = EventTypeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = EventTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Event Type created successfully.")
            return redirect("eventtype_list")
        messages.error(
            request,
            "There was an error creating the Event Type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class EventTypeUpdateView(LoginRequiredMixin, View):
    template_name = "forms/eventtype_form.html"

    def get(self, request, pk):
        eventtype = get_object_or_404(EventType, pk=pk)
        form = EventTypeForm(instance=eventtype)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        eventtype = get_object_or_404(EventType, pk=pk)
        form = EventTypeForm(request.POST, instance=eventtype)
        if form.is_valid():
            form.save()
            messages.success(request, "Event Type Capacity updated successfully.")
            return redirect("eventtype_list")
        messages.error(
            request,
            "There was an error updating the Event type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class EventTypeDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        eventtype = get_object_or_404(EventType, pk=pk)
        eventtype.delete()
        messages.success(request, "Event Type successfully deleted.")
        return redirect("eventtype_list")

    def post(self, request, pk):
        eventtype = get_object_or_404(EventType, pk=pk)
        eventtype.delete()
        messages.success(request, "Event Type successfully deleted.")
        return redirect("eventtype_list")


class EventTypeListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/EventType.html"

    def get(self, request):
        eventtypes = EventType.objects.all()
        return render(
            request,
            self.template_name,
            {
                "eventtypes": eventtypes,
                "breadcrumb": {"parent": "General Settings", "child": "Event Types"},
            },
        )


######################################################### News Module ###############################################
class NewsListView(LoginRequiredMixin, View):
    template_name = "Admin/News_List.html"

    def get(self, request):
        news = News.objects.all()
        return render(
            request,
            self.template_name,
            {
                "news": news,
                "breadcrumb": {"child": "News List"},
            },
        )


class NewsCreateView(View):
    def post(self, request):
        title_en = request.POST.get("title_en")
        description_en = request.POST.get("description_en")
        title_ar = request.POST.get("title_ar")
        description_ar = request.POST.get("description_ar")

        if not title_en or not description_ar or not title_ar or not description_en:
            messages.error(request, "Title and Description are required.")
            return redirect("news_list")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "news"))
            image_name = fs.save(image_file.name, image_file)
            image_name = "news/" + image_name

        news = News.objects.create(
            title_en=title_en,
            title_ar=title_ar,
            description_ar=description_ar,
            description_en=description_en,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "News created successfully.")
        return redirect("news_list")


class NewsEditView(View):
    template_name = "Admin/News_List.html"

    def post(self, request, news_id):
        news_item = get_object_or_404(News, id=news_id)

        title_en = request.POST.get("title_en")
        description_en = request.POST.get("description_en")
        title_ar = request.POST.get("title_ar")
        description_ar = request.POST.get("description_ar")

        if not title_en or not description_ar or not title_ar or not description_en:
            messages.error(request, "Title and Description are required.")
            return redirect("news_list")

        news_item.title_en = title_en
        news_item.title_ar = title_ar
        news_item.description_ar = description_ar
        news_item.description_en = description_en

        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "news"))
            if news_item.image and news_item.image.path:
                old_image_path = news_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            news_item.image = "news/" + image_name

        news_item.save()

        messages.success(request, "News updated successfully.")
        return redirect("news_list")


class NewsDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.delete()
        messages.success(request, "News Deleted Successfully.")
        return redirect("news_list")


############################################################## Partners Module ###############################################
class PartnersListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/Partners_List.html"

    def get(self, request):
        partners = Partners.objects.all()
        return render(
            request,
            self.template_name,
            {
                "partners": partners,
                "breadcrumb": {"child": "Partners List"},
            },
        )


class PartnersCreateView(View):
    def post(self, request):
        title = request.POST.get("title")

        if not title:
            messages.error(request, "Partner Title is required.")
            return redirect("partners_list")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "partners")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "partners/" + image_name

        partners = Partners.objects.create(
            title=title,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Partners created successfully.")
        return redirect("partners_list")


class PartnersEditView(View):
    template_name = "Admin/General_Settings/Partners_List.html"

    def post(self, request, partners_id):
        partners_item = get_object_or_404(Partners, id=partners_id)

        title = request.POST.get("title")

        if not title:
            messages.error(request, "Partner Title is required.")
            return redirect("partners_list")

        partners_item.title = title
        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "partners")
            )
            if partners_item.image and partners_item.image.path:
                old_image_path = partners_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            partners_item.image = "partners/" + image_name

        partners_item.save()

        messages.success(request, "Partners updated successfully.")
        return redirect("partners_list")


class PartnersDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        partners = get_object_or_404(Partners, pk=pk)
        partners.delete()
        messages.success(request, "Partners Deleted Successfully.")
        return redirect("partners_list")


############################################################ Global Clients Module ###############################################
class Global_ClientsListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/Global_Clients_List.html"

    def get(self, request):
        global_clients = Global_Clients.objects.all()
        return render(
            request,
            self.template_name,
            {
                "global_clients": global_clients,
                "breadcrumb": {"child": "Global-Clients List"},
            },
        )


class Global_ClientsCreateView(View):
    def post(self, request):
        title = request.POST.get("title")

        if not title:
            messages.error(request, "Global Clients Title is required.")
            return redirect("global_clients_list")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "global_clients")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "global_clients/" + image_name

        global_clients = Global_Clients.objects.create(
            title=title,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Global Client created successfully.")
        return redirect("global_clients_list")


class Global_ClientsEditView(View):
    template_name = "Admin/General_Settings/Global_Clients_List.html"

    def post(self, request, global_clients_id):
        global_clients_item = get_object_or_404(Global_Clients, id=global_clients_id)

        title = request.POST.get("title")

        if not title:
            messages.error(request, "Global Client Title is required.")
            return redirect("global_clients_list")

        global_clients_item.title = title
        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "global_clients")
            )
            if global_clients_item.image and global_clients_item.image.path:
                old_image_path = global_clients_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            global_clients_item.image = "global_clients/" + image_name

        global_clients_item.save()

        messages.success(request, "Global Client updated successfully.")
        return redirect("global_clients_list")


class Global_ClientsDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        global_clients = get_object_or_404(Global_Clients, pk=pk)
        global_clients.delete()
        messages.success(request, "Global Client Deleted Successfully.")
        return redirect("global_clients_list")


################################################################# Tryout Club Module ###############################################
class Tryout_ClubListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/Tryout_Club_List.html"

    def get(self, request):
        tryout_club = Tryout_Club.objects.all()
        return render(
            request,
            self.template_name,
            {
                "tryout_club": tryout_club,
                "breadcrumb": {"child": "Tryout Club List"},
            },
        )


class Tryout_ClubCreateView(View):
    def post(self, request):
        title = request.POST.get("title")

        if not title:
            messages.error(request, "Tryout Club Title is required.")
            return redirect("tryout_club_list")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "tryout_club")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "tryout_club/" + image_name

        tryout_club = Tryout_Club.objects.create(
            title=title,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Tryout Club created successfully.")
        return redirect("tryout_club_list")


class Tryout_ClubEditView(View):
    template_name = "Admin/General_Settings/Tryout_Club_List.html"

    def post(self, request, tryout_club_id):
        tryout_club_item = get_object_or_404(Tryout_Club, id=tryout_club_id)

        title = request.POST.get("title")

        if not title:
            messages.error(request, "Tryout Club Title is required.")
            return redirect("tryout_club_list")

        tryout_club_item.title = title
        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "tryout_club")
            )
            if tryout_club_item.image and tryout_club_item.image.path:
                old_image_path = tryout_club_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            tryout_club_item.image = "tryout_club/" + image_name

        tryout_club_item.save()

        messages.success(request, "Tryout Club updated successfully.")
        return redirect("tryout_club_list")


class Tryout_ClubDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tryout_club = get_object_or_404(Tryout_Club, pk=pk)
        tryout_club.delete()
        messages.success(request, "Tryout Club Deleted Successfully.")
        return redirect("tryout_club_list")


#################################################################### Inquires Module ###############################################
class InquireListView(LoginRequiredMixin, View):
    template_name = "Admin/Inquire_List.html"

    def get(self, request):
        inquire = Inquire.objects.all().order_by("-id")
        print(inquire)
        return render(
            request,
            self.template_name,
            {
                "inquire": inquire,
                "breadcrumb": {"child": "List of Inquires"},
            },
        )


################################################################ Testimonial Module ###############################################
class TestimonialListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/Testimonial_List.html"

    def get(self, request):
        testimonial = Testimonial.objects.all()
        return render(
            request,
            self.template_name,
            {
                "testimonial": testimonial,
                "breadcrumb": {"child": "Testimonial List"},
            },
        )


class TestimonialCreateView(View):
    def post(self, request):
        name_en = request.POST.get("name_en")
        designation_en = request.POST.get("designation_en")
        content_en = request.POST.get("content_en")
        rattings = request.POST.get("rattings")
        name_ar = request.POST.get("name_ar")
        designation_ar = request.POST.get("designation_ar")
        content_ar = request.POST.get("content_ar")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "testimonial")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "testimonial/" + image_name

        testimonial = Testimonial.objects.create(
            name_en=name_en,
            designation_en=designation_en,
            content_en=content_en,
            name_ar=name_ar,
            designation_ar=designation_ar,
            content_ar=content_ar,
            rattings=rattings,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Testimonial Created successfully.")
        return redirect("testimonial_list")


class TestimonialEditView(View):
    template_name = "Admin/General_Settings/Testimonial_List.html"

    def post(self, request, testimonial_id):
        testimonial_item = get_object_or_404(Testimonial, id=testimonial_id)

        name_en = request.POST.get("name_en")
        designation_en = request.POST.get("designation_en")
        content_en = request.POST.get("content_en")
        rattings = request.POST.get("rattings")
        name_ar = request.POST.get("name_ar")
        designation_ar = request.POST.get("designation_ar")
        content_ar = request.POST.get("content_ar")

        testimonial_item.name_en = name_en
        testimonial_item.designation_en = designation_en
        testimonial_item.content_en = content_en
        testimonial_item.name_ar = name_ar
        testimonial_item.designation_ar = designation_ar
        testimonial_item.content_ar = content_ar
        testimonial_item.rattings = rattings
        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "testimonial")
            )
            if testimonial_item.image and testimonial_item.image.path:
                old_image_path = testimonial_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            testimonial_item.image = "testimonial/" + image_name

        testimonial_item.save()

        messages.success(request, "Testimonial updated successfully.")
        return redirect("testimonial_list")


class TestimonialDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        testimonial = get_object_or_404(Testimonial, pk=pk)
        testimonial.delete()
        messages.success(request, "Testimonial Deleted Successfully.")
        return redirect("testimonial_list")


################################################################ Team_Members Module ###############################################
class Team_MembersListView(LoginRequiredMixin, View):
    template_name = "Admin/Team_Members_List.html"

    def get(self, request):
        team_members = Team_Members.objects.all()
        return render(
            request,
            self.template_name,
            {
                "team_members": team_members,
                "breadcrumb": {"child": "Team Members List"},
            },
        )


class Team_MembersCreateView(View):
    def post(self, request):
        name_en = request.POST.get("name_en")
        designations_en = request.POST.get("designations_en")
        name_ar = request.POST.get("name_ar")
        designations_ar = request.POST.get("designations_ar")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "team_members")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "team_members/" + image_name

        team_members = Team_Members.objects.create(
            name_en=name_en,
            designations_en=designations_en,
            name_ar=name_ar,
            designations_ar=designations_ar,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Team Member created successfully.")
        return redirect("team_members_list")


class Team_MembersEditView(View):
    template_name = "Admin/Team_Members_List.html"

    def post(self, request, team_members_id):
        team_members_item = get_object_or_404(Team_Members, id=team_members_id)

        name_en = request.POST.get("name_en")
        designations_en = request.POST.get("designations_en")
        name_ar = request.POST.get("name_ar")
        designations_ar = request.POST.get("designations_ar")

        team_members_item.designations_en = designations_en
        team_members_item.name_en = name_en
        team_members_item.name_ar = name_ar
        team_members_item.designations_ar = designations_ar

        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "team_members")
            )
            if team_members_item.image and team_members_item.image.path:
                old_image_path = team_members_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            team_members_item.image = "team_members/" + image_name

        team_members_item.save()

        messages.success(request, "Team Member updated successfully.")
        return redirect("team_members_list")


class Team_MembersDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        team_members = get_object_or_404(Team_Members, pk=pk)
        team_members.delete()
        messages.success(request, "Team Member Deleted Successfully.")
        return redirect("team_members_list")


################################################################ App_Feature Module ###############################################
class App_FeatureListView(LoginRequiredMixin, View):
    template_name = "Admin/App_Feature_List.html"

    def get(self, request):
        app_feature = App_Feature.objects.all()
        return render(
            request,
            self.template_name,
            {
                "app_feature": app_feature,
                "breadcrumb": {"child": "App Feature List"},
            },
        )


class App_FeatureCreateView(View):
    def post(self, request):
        title_en = request.POST.get("title_en")
        sub_title_en = request.POST.get("sub_title_en")
        title_ar = request.POST.get("title_ar")
        sub_title_ar = request.POST.get("sub_title_ar")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "app_feature")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "app_feature/" + image_name

        app_feature = App_Feature.objects.create(
            title_en=title_en,
            sub_title_en=sub_title_en,
            title_ar=title_ar,
            sub_title_ar=sub_title_ar,
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "App Feature created successfully.")
        return redirect("app_feature_list")


class App_FeatureEditView(View):
    template_name = "Admin/App_Feature_List.html"

    def post(self, request, app_feature_id):
        app_feature_item = get_object_or_404(App_Feature, id=app_feature_id)

        title_en = request.POST.get("title_en")
        sub_title_en = request.POST.get("sub_title_en")
        title_ar = request.POST.get("title_ar")
        sub_title_ar = request.POST.get("sub_title_ar")

        app_feature_item.title_en = title_en
        app_feature_item.sub_title_en = sub_title_en
        app_feature_item.title_ar = title_ar
        app_feature_item.sub_title_ar = sub_title_ar

        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "app_feature")
            )
            if app_feature_item.image and app_feature_item.image.path:
                old_image_path = app_feature_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            app_feature_item.image = "app_feature/" + image_name

        app_feature_item.save()

        messages.success(request, "App Feature updated successfully.")
        return redirect("app_feature_list")


class App_FeatureDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        app_feature = get_object_or_404(App_Feature, pk=pk)
        app_feature.delete()
        messages.success(request, "App Feature Deleted Successfully.")
        return redirect("app_feature_list")


#################################################   Slider_Content CRUD Views  #######################################################
class Slider_ContentCreateView(LoginRequiredMixin, View):
    template_name = "forms/slider_content_form.html"

    def get(self, request):
        form = Slider_ContentForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = Slider_ContentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Slider Content Created successfully.")
            return redirect("slider_content_list")
        messages.error(
            request,
            "There was an error creating the Slider Content. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class Slider_ContentUpdateView(LoginRequiredMixin, View):
    template_name = "forms/slider_content_form.html"

    def get(self, request, pk):
        slider_content = get_object_or_404(Slider_Content, pk=pk)
        form = Slider_ContentForm(instance=slider_content)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        slider_content = get_object_or_404(Slider_Content, pk=pk)
        form = Slider_ContentForm(request.POST, instance=slider_content)
        if form.is_valid():
            form.save()
            messages.success(request, "Slider Content Updated Successfully.")
            return redirect("slider_content_list")
        messages.error(
            request,
            "There was an error updating the  Slider Content. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})


class Slider_ContentDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        slider_content = get_object_or_404(Slider_Content, pk=pk)
        slider_content.delete()
        messages.success(request, "Slider Content Successfully Deleted.")
        return redirect("slider_content_list")

    def post(self, request, pk):
        slider_content = get_object_or_404(Slider_Content, pk=pk)
        slider_content.delete()
        messages.success(request, "Slider Content Successfully Deleted.")
        return redirect("slider_content_list")


class Slider_ContentListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/Slider_Content.html"

    def get(self, request):
        slider_contents = Slider_Content.objects.all()
        return render(
            request,
            self.template_name,
            {
                "slider_contents": slider_contents,
                "breadcrumb": {"child": "Slider Content"},
            },
        )



########################## CMS PAGES #################################        
class CMSPages(LoginRequiredMixin, View):
    template_name = "Admin/cmspages.html"
    

    def get(self,request):
        
        cms_pages_name = cms_pages.objects.all()
        
        context = {
            'cms_pages_name': cms_pages_name
        }
        
        
        return render(request, self.template_name,context)
    
 
 
 

 
######################################## cms_contact_page  ##############################################################      
class cms_contactpage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/contactus.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(name_en = "Contacts")
        
        context = {
            'data':dataFilter,
        }
        
        return render(
            request,
            self.template_name,
            context
        )
        
@csrf_exempt
def savecontactpage(request):
        try:
            
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('heading_title_en')
                heading_title_ar  = request.POST.get('heading_title_ar')
                heading_content_en = request.POST.get('heading_content_en')
                heading_content_ar = request.POST.get('heading_content_ar')
                sub_heading_title_en = request.POST.get('sub_heading_title_en')
                sub_heading_title_ar = request.POST.get('sub_heading_title_ar')
                sub_heading_sub_title_en= request.POST.get('sub_heading_sub_title_en')
                sub_heading_sub_title_ar= request.POST.get('sub_heading_sub_title_ar')
                country_name_en= request.POST.get('country_name_en')
                country_name_ar= request.POST.get('country_name_ar')
                sub_heading_name_en= request.POST.get('sub_heading_name_en')
                sub_heading_name_ar= request.POST.get('sub_heading_name_ar')
                sub_heading_title_2_en = request.POST.get('sub_heading_title_2_en')
                sub_heading_title_2_ar = request.POST.get('sub_heading_title_2_ar') 
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                #images
                dom = "Done"
                imageName = []


                
                try:
                    contactussave = cms_pages.objects.get(name_en = "Contacts")


                    if 'banner' in request.FILES:
                        print("yes")
                        
                        heading_banner = request.FILES.get('banner',None)
                        if heading_banner:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_banner.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in heading_banner.chunks():
                                        destination.write(chunk)
                                        imageName.append(heading_banner.name)
                                        contactussave.heading_banner = heading_banner

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass            
                               
                    if 'mailicon' in request.FILES:
                        

                            try:
                                mailicon = request.FILES.get('mailicon',None)

                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', mailicon.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in  mailicon.chunks():
                                        destination.write(chunk)
                                        imageName.append(mailicon.name)
                                        contactussave.sub_section_2_1_icon = mailicon

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass               
                    
                    
                    
                    
                
                    
                     
                    
                    if 'phoneicon' in request.FILES:

                        try:
                            phoneicon = request.FILES.get('phoneicon',None)

                            save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', phoneicon.name)
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)

                            # Save the file
                            with open(save_path, 'wb+') as destination:
                                for chunk in phoneicon.chunks():
                                    destination.write(chunk)
                                    imageName.append(phoneicon.name)
                                    contactussave.sub_section_2_2_icon = phoneicon
                        except Exception as e:
                            dom = str(e)   
                    else:
                        pass                    
                            
                        
                        #section 1
                    contactussave.heading_title_en = heading_title_en
                    contactussave.heading_title_ar = heading_title_ar
                    contactussave.heading_content_en = heading_content_en
                    contactussave.heading_content_ar = heading_content_ar
                    #contactussave.heading_banner = heading_banner
                        
                        #section 2 
                    contactussave.section_2_heading_en = sub_heading_title_en
                    contactussave.section_2_heading_ar = sub_heading_title_ar
                    contactussave.section_2_title_en = sub_heading_sub_title_en
                    contactussave.section_2_title_ar = sub_heading_sub_title_ar
                        #section 2 country_name
                    contactussave.section_2_country_name_en = country_name_en
                    contactussave.section_2_country_name_ar = country_name_ar

                        #section 2 mailicon and phoneicon
                    #contactussave.sub_section_2_1_icon = mailicon
                    #contactussave.sub_section_2_2_icon = phoneicon

                        #section 3 
                    contactussave.section_3_heading_en = sub_heading_name_en
                    contactussave.section_3_heading_ar = sub_heading_name_ar
                    contactussave.section_3_title_en  = sub_heading_title_2_en
                    contactussave.section_3_title_ar = sub_heading_title_2_ar
                        
                        #seo data
                    contactussave.meta_title_en = seo_title_en
                    contactussave.meta_title_ar = seo_title_ar
                    contactussave.meta_content_en = seo_content_en
                    contactussave.meta_content_ar = seo_content_ar
                        
                    contactussave.save()
                    dom = "True"
                    
                    messages.success(request, "Contact Page Updated Successfully")
                    #return redirect("cms_contactpage")
                
                except Exception as e:
                    messages.error(request,"Error Saving!")      
                        
                    
                    
                      
                        
                        
                response_data = {
                        'status': 'success',
                        'message': 'Data and uploaded successfully',
                        'heading_title_en': dom                    }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
            response_data = {'status': 'error', 'message': str(e)}

            return JsonResponse(response_data) 

    
#cms_about_page     
class cms_aboutpage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/aboutus.html"

    
    def get(self, request):
        dataFilter = cms_pages.objects.get(id="7")

        context = {
            'data':dataFilter
        }
        return render(
            request,
            self.template_name,
            context
            
        )
        
@csrf_exempt
def saveAboutUspage(request):
        try:
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('heading_title_en')
                heading_title_ar  = request.POST.get('heading_title_ar')
                #heading_section_video  = request.FILES['heading_section_video']
                heading_content_en  = request.POST.get('heading_content_en')
                heading_content_ar  = request.POST.get('heading_content_ar')
                heading_year_en  = request.POST.get('heading_year_en')
                heading_year_ar  = request.POST.get('heading_year_ar')
                sub_heading_en  = request.POST.get('sub_heading_en')
                sub_heading_ar  = request.POST.get('sub_heading_ar')
                whoweare_title_en  = request.POST.get('whoweare_title_en')
                whoweare_title_ar  = request.POST.get('whoweare_title_ar')
                global_client_heading_en  = request.POST.get('global_client_heading_en')
                global_client_heading_ar  = request.POST.get('global_client_heading_ar')
                seo_title_en  = request.POST.get('seo_title_en')
                seo_title_ar  = request.POST.get('seo_title_ar')
                seo_content_en  = request.POST.get('seo_content_en')
                seo_content_ar  = request.POST.get('seo_content_ar')
                #images
                dom = "Done"
                imageName = []
                
                
                try:
                    aboutussave = cms_pages.objects.get(id = "7")


                    if 'heading_video' in request.FILES:
                        
                        heading_video = request.FILES.get('heading_video',None)
                        if heading_video:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_video.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in heading_video.chunks():
                                        destination.write(chunk)
                                        imageName.append(heading_video.name)
                                        aboutussave.heading_video = heading_video

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass   
                    
                    if 'testi_icon' in request.FILES:
                        
                        testi_icon = request.FILES.get('testi_icon',None)
                        if testi_icon:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', testi_icon.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in testi_icon.chunks():
                                        destination.write(chunk)
                                        imageName.append(testi_icon.name)
                                        aboutussave.section_3_feature_icons = testi_icon

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass  
                    #section1
                    aboutussave.heading_title_en = heading_title_en
                    aboutussave.heading_title_ar = heading_content_ar
                    aboutussave.heading_content_en = heading_content_en
                    aboutussave.heading_content_ar = heading_content_ar
                    aboutussave.heading_year_title_en =heading_year_en
                    aboutussave.heading_year_title_ar =heading_year_ar
                    #section_2
                    aboutussave.section_2_heading_en = sub_heading_en
                    aboutussave.section_2_heading_ar = sub_heading_ar
                    aboutussave.section_2_title_en = whoweare_title_en
                    aboutussave.section_2_title_ar = whoweare_title_ar
                    #section_3
                    aboutussave.section_3_heading_en = global_client_heading_en
                    aboutussave.section_3_heading_ar = global_client_heading_ar
                    #meta section
                    aboutussave.meta_title_en = seo_title_en
                    aboutussave.meta_title_ar = seo_title_ar
                    aboutussave.meta_content_ar = seo_content_en
                    aboutussave.meta_content_en = seo_content_ar

                    aboutussave.save()
                    dom = "True"
                    messages.success(request, "About Page Updated Successfully")



                except Exception as e:
                    messages.error(request,str(e))      
                    
                

                    
                
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': dom
                        }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 

#cms_about_page     
class cms_newsPage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/news.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(id = "4")
        
        context = {
            'data':dataFilter
        }

        return render(
            request,
            self.template_name,
            context
            
        )
              
@csrf_exempt
def savenewspage(request):
        try:
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('heading_title_en')
                heading_title_ar  = request.POST.get('heading_title_ar')
                #heading_section_video  = request.FILES['heading_section_video']
                heading_content_en  = request.POST.get('heading_content_en')
                heading_content_ar  = request.POST.get('heading_content_ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                
                               
                dom = "Done"
                imageName = []
                
                try:
                    savenews = cms_pages.objects.get(id = "4")


                    if 'heading_banner' in request.FILES:
                        
                        heading_banner = request.FILES.get('heading_banner',None)
                        if heading_banner:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_banner.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in heading_banner.chunks():
                                        destination.write(chunk)
                                        imageName.append(heading_banner.name)
                                        savenews.heading_banner = heading_banner

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass   
                    
                    savenews.heading_title_en = heading_title_en
                    savenews.heading_title_ar = heading_title_ar
                    savenews.heading_content_en = heading_content_en
                    savenews.heading_content_ar = heading_content_ar
                    savenews.meta_title_en = seo_title_en
                    savenews.meta_title_ar = seo_title_ar
                    savenews.meta_content_en = seo_content_en
                    savenews.meta_content_ar = seo_content_ar

                    savenews.save()
                    
                    dom = "True"
                    
                    messages.success(request, "News Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': dom
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
                   
#cms_about_page     
class cms_successStory(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/successtory.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(id="3")
        
        context = {
            'data':dataFilter
        }
        
        return render(
            request,
            self.template_name,
            context
    )
        
@csrf_exempt
def saveSucessStorypage(request):
        try:
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('heading_title_en')
                heading_title_ar  = request.POST.get('heading_title_ar')
                #heading_section_video  = request.FILES['heading_section_video']
                heading_content_en  = request.POST.get('heading_content_en')
                heading_content_ar  = request.POST.get('heading_content_ar')
                tryoutclubs_title_en  = request.POST.get('tryoutclubs_title_en')
                tryoutclubs_title_ar  = request.POST.get('tryoutclubs_title_ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                dom = "Done"
                imageName = []
                
                try:
                    successstorysave = cms_pages.objects.get(id = "3")


                    if 'heading_banner' in request.FILES:
                        
                        heading_banner = request.FILES.get('heading_banner',None)
                        if heading_banner:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_banner.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in heading_banner.chunks():
                                        destination.write(chunk)
                                        imageName.append(heading_banner.name)
                                        successstorysave.heading_banner = heading_banner

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass   
                    
                    successstorysave.heading_title_en = heading_title_en
                    successstorysave.heading_title_ar = heading_title_ar
                    successstorysave.heading_content_en = heading_content_en
                    successstorysave.heading_content_ar = heading_content_ar
                    successstorysave.section_2_title_en = tryoutclubs_title_en
                    successstorysave.section_2_title_ar = tryoutclubs_title_ar
                    successstorysave.meta_title_en = seo_title_en
                    successstorysave.meta_title_ar = seo_title_ar
                    successstorysave.meta_content_en = seo_content_en
                    successstorysave.meta_content_ar = seo_content_ar

                    successstorysave.save()
                    
                    dom = "True"
                    
                    messages.success(request, "Success Story Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': dom
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 

#cms_about_page     
class cms_termcondition(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/term&condition.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(name_en = "Terms & Condition")
        
        context = {
            'data':dataFilter
        }
        
        return render(
            request,
            self.template_name,
            context
            
    )
        
@csrf_exempt
def savetermconditionpage(request):
        try:
            if request.method == "POST":
                saving_error = "None"
                #text
                tc_title_en  = request.POST.get('tc-title-en')
                tc_title_ar  = request.POST.get('tc-title-ar')
                tc_content_en  = request.POST.get('tc-content-en')
                tc_content_ar  = request.POST.get('tc-content-ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                try:
                    termcondition = cms_pages.objects.get(name_en = "Terms & Condition")
                    termcondition.heading_title_en = tc_title_en
                    termcondition.heading_title_ar = tc_title_ar
                    termcondition.heading_content_en = tc_content_en
                    termcondition.heading_content_ar = tc_content_ar
                    termcondition.meta_title_en = seo_title_en
                    termcondition.meta_title_ar = seo_title_ar
                    termcondition.meta_content_en = seo_content_en
                    termcondition.meta_content_ar = seo_content_ar
                     
                    termcondition.save()

                    messages.success(request, "Term and Condition Page Updated Successfully")


                except Exception as e:
                    messages.error(request, str(e))

                    saving_error = str(e)
                    
            
                    response_data = {
                            'status': 'success',
                            'message': saving_error,
                    }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
        
#cms privacy policy page     
class cms_privacypolicy(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/privacypolicy.html"

    def get(self, request):
        dataFilter = cms_pages.objects.get(name_en="Privacy Policy")
        
        context ={
            'data': dataFilter
        }
        return render(
            request,
            self.template_name,
            context
            
    )
@csrf_exempt
def saveprivacypolicypage(request):
        
        try:
            if request.method == "POST":
                saving_error = "None"
                #text
                pp_title_en  = request.POST.get('tc-title-en')
                pp_title_ar  = request.POST.get('tc-title-ar')
                pp_content_en  = request.POST.get('tc-content-en')
                pp_content_ar  = request.POST.get('tc-content-ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                try:
                    privacypolicy = cms_pages.objects.get(id = "10")
                    privacypolicy.heading_title_en = pp_title_en
                    privacypolicy.heading_title_ar = pp_title_ar
                    privacypolicy.heading_content_en = pp_content_en
                    privacypolicy.heading_content_ar = pp_content_ar
                    privacypolicy.meta_title_en = seo_title_en
                    privacypolicy.meta_title_ar = seo_title_ar
                    privacypolicy.meta_content_en = seo_content_en
                    privacypolicy.meta_content_ar = seo_content_ar
                     
                    privacypolicy.save()

                    messages.success(request, "Privacy Policy Page Updated Successfully")

                except Exception as e:
                    print(str(e))
                    messages.error(request,str(e))
                    
            
                    response_data = {
                            'status': 'success',
                            'message': saving_error,
                    }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
               
#cms term and service  
class cms_termandserice(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/term&service.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(name_en='Terms of Services')
        
        context = {
            'data':dataFilter,
        }
        dataFilter.meta_title_en
        print(dataFilter.heading_title_en)
        return render(
            request,
            self.template_name,
            context
            
    ) 
        
#save term and condition        
@csrf_exempt
def savetermservicepage(request):
        
        try:
            if request.method == "POST":
                saving_error = "None"
                dom = "Done"

                #text
                ts_title_en  = request.POST.get('ts-title-en')
                ts_title_ar  = request.POST.get('ts-title-ar')
                ts_content_en  = request.POST.get('ts-content-en')
                ts_content_ar  = request.POST.get('ts-content-ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                try:
                    termservice = cms_pages.objects.get(name_en = "Terms of Services")
                    termservice.heading_title_en = ts_title_en
                    termservice.heading_title_ar = ts_title_ar
                    termservice.heading_content_en = ts_content_en
                    termservice.heading_content_ar = ts_content_ar
                    termservice.meta_title_en = seo_title_en
                    termservice.meta_title_ar = seo_title_ar
                    termservice.meta_content_en = seo_content_en
                    termservice.meta_content_ar = seo_content_ar
                     
                    termservice.save()

                    dom = "True"

                    messages.success(request, "Term and service Page Updated Successfully")

                except Exception as e:
                    messages.error(request,str(e))
                    saving_error = str(e)
                    
            
                    response_data = {
                            'status': 'success',
                            'message': saving_error,
                    }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
                   
        
#cms news detail  
class cms_newsdetail(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/newsdetail.html"

    def get(self, request):
        dataFilter = cms_pages.objects.get(id="5")
        
        context = {
            'data':dataFilter
        }
        return render(
            request,
            self.template_name,
            context
            
    )   
        
#cms news detail  
@csrf_exempt
def savenewsdetail(request):
        try:
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('nd_title_en')
                heading_title_ar  = request.POST.get('nd_title_ar')
                #heading_section_video  = request.FILES['heading_section_video']
                heading_content_en  = request.POST.get('nd_content_en')
                heading_content_ar  = request.POST.get('nd_content_ar')
                seo_title_en  = request.POST.get('seo_title_en')
                seo_title_ar  = request.POST.get('seo_title_ar')
                seo_content_en  = request.POST.get('seo_content_en')
                seo_content_ar  = request.POST.get('seo_content_ar')
                
                dom = "Done"
                imageName = []
                
                try:
                    savenewsdetail = cms_pages.objects.get(id = "5")


                    if 'heading_banner' in request.FILES:
                        
                        heading_banner = request.FILES.get('heading_banner',None)
                        if heading_banner:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_banner.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in heading_banner.chunks():
                                        destination.write(chunk)
                                        imageName.append(heading_banner.name)
                                        savenewsdetail.heading_banner = heading_banner

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass   
                    
                    savenewsdetail.section_2_title_en = heading_title_en
                    savenewsdetail.section_2_title_ar = heading_title_ar
                    savenewsdetail.section_2_content_en = heading_content_en
                    savenewsdetail.section_2_content_ar = heading_content_ar
                    savenewsdetail.meta_title_en = seo_title_en
                    savenewsdetail.meta_title_ar = seo_title_ar
                    savenewsdetail.meta_content_en = seo_content_en
                    savenewsdetail.meta_content_ar = seo_content_ar

                    savenewsdetail.save()
                    
                    dom = "True"
                    
                    messages.success(request, "News Detail Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': dom
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 

        
#cms descovery page
class cms_discoverypage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/discovery.html"

    def get(self, request):
        
        return render(
            request,
            self.template_name,
            
    )  
#cms Advertise page
class cms_advertisepage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/advertise.html"

    def get(self, request):
        
        return render(
            request,
            self.template_name,
            
    )                                 

#home page
class cms_homepage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/home.html"

    def get(self, request):
        
        return render(
            request,
            self.template_name,
            
    )              