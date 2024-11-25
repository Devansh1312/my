import os
from django.shortcuts import render, redirect, get_object_or_404
from django import views
from .forms import *
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, Http404 ,HttpResponseNotAllowed
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
import sys
from functools import wraps
from django.core.files.storage import FileSystemStorage
import json
from FutureStarAPI.models import *
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarTournamentApp.models import *
from FutureStarGameSystem.models import *
from django.utils.safestring import mark_safe
from django.db.models import F, Case, When, IntegerField
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist


def user_role_check(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.role_id != 1:
            messages.error(request, "You do not have access to this site.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view




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


@method_decorator(user_role_check, name='dispatch')
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
    return redirect("index")


##################################################### User Profile View ###############################################################
@method_decorator(user_role_check, name='dispatch')
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


@method_decorator(user_role_check, name='dispatch')
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
            form = UserUpdateProfileForm(
                request.POST, instance=user, files=request.FILES
            )
            if form.is_valid():
                # Handle profile picture update
                # Initialize FileSystemStorage for profile pictures and card headers
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'profile_pics'))
                card_fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'card_header'))

                # Handle profile picture
                if "profile_picture" in request.FILES:
                    # Remove old profile picture if it exists
                    if user.profile_picture:
                        old_profile_picture_path = os.path.join(
                            settings.MEDIA_ROOT, str(user.profile_picture)  # Convert to string
                        )
                        if os.path.isfile(old_profile_picture_path):
                            os.remove(old_profile_picture_path)

                    # Save new profile picture
                    profile_picture_file = request.FILES["profile_picture"]
                    file_extension = profile_picture_file.name.split('.')[-1]
                    unique_suffix = get_random_string(8)
                    profile_picture_filename = f"{request.user.id}_{unique_suffix}.{file_extension}"
                    fs.save(profile_picture_filename, profile_picture_file)
                    user.profile_picture = os.path.join(
                        "profile_pics", profile_picture_filename
                    )
                elif "profile_picture-clear" in request.POST:
                    # Clear the profile picture field
                    if user.profile_picture:
                        old_profile_picture_path = os.path.join(
                            settings.MEDIA_ROOT, str(user.profile_picture)  # Convert to string
                        )
                        if os.path.isfile(old_profile_picture_path):
                            os.remove(old_profile_picture_path)
                    user.profile_picture = None

                # Handle card_header
                if "card_header" in request.FILES:
                    # Remove old card header if it exists
                    if user.card_header:
                        old_card_header_path = os.path.join(
                            settings.MEDIA_ROOT, str(user.card_header)  # Convert to string
                        )
                        if os.path.isfile(old_card_header_path):
                            os.remove(old_card_header_path)

                    # Save new card header
                    card_header_file = request.FILES["card_header"]
                    file_extension = card_header_file.name.split('.')[-1]
                    unique_suffix = get_random_string(8)
                    card_header_filename = f"card_header_{unique_suffix}.{file_extension}"
                    card_fs.save(card_header_filename, card_header_file)
                    user.card_header = os.path.join(
                        "card_header", card_header_filename
                    )
                elif "card_header-clear" in request.POST:
                    # Clear the card header field
                    if user.card_header:
                        old_card_header_path = os.path.join(
                            settings.MEDIA_ROOT, str(user.card_header)  # Convert to string
                        )
                        if os.path.isfile(old_card_header_path):
                            os.remove(old_card_header_path)
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
@method_decorator(user_role_check, name='dispatch')
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

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "System_Settings"))

        errors = {}
        success = False

        try:
            # Handle file uploads: Fav Icon, Footer Logo, Header Logo, and Images
            file_fields = {
                "fav_icon": "fav_icon",
                "footer_logo": "footer_logo",
                "header_logo": "header_logo",
                "splash_screen": "splash_screen",
                "intro1_image": "intro1_image",
                "intro2_image": "intro2_image",  # Corrected the typo in code
                "intro3_image": "intro3_image",
            }

            for field_name, field_label in file_fields.items():
                if field_name in request.FILES:
                    field_file = request.FILES[field_name]
                    current_file = getattr(system_settings, field_label, None)

                    # Remove old file if it exists
                    if current_file:
                        old_file_path = os.path.join(settings.MEDIA_ROOT, current_file)
                        if os.path.isfile(old_file_path):
                            os.remove(old_file_path)

                    # Save the new file
                    file_extension = field_file.name.split('.')[-1]
                    unique_suffix = get_random_string(8)
                    file_filename = f"{field_label}_{unique_suffix}.{file_extension}"
                    fs.save(file_filename, field_file)
                    setattr(system_settings, field_label, os.path.join("System_Settings", file_filename))

            # Handle text fields: intro1_text, intro2_text, intro3_text
            text_fields = ['intro1_text', 'intro2_text', 'intro3_text']
            for field_name in text_fields:
                field_value = request.POST.get(field_name)
                if field_value:
                    setattr(system_settings, field_name, field_value)

            # Handle other settings fields from request.POST
            settings_fields = {
                "website_name_english": "This field is required.",
                "website_name_arabic": "This field is required.",
                "phone": "This field is required.",
                "email": "This field is required.",
                "address": "This field is required.",
                "currency_symbol": "This field is required.",
                "event_convenience_fee": "This field is required.",
                "happy_user": "This field is required.",
                "line_of_code": "This field is required.",
                "downloads": "This field is required.",
                "app_rate": "This field is required.",
                "instagram": None,
                "facebook": None,
                "twitter": None,
                "linkedin": None,
                "pinterest": None,
                "years_of_experience": None,
                "project_completed": None,
                "proffesioan_team_members": None,
                "awards_winning": None,
            }

            for field, error_message in settings_fields.items():
                field_value = request.POST.get(field)
                if not field_value and error_message:
                    errors[field] = error_message
                else:
                    setattr(system_settings, field, field_value)

            # Check if there are any errors
            if errors:
                messages.error(request, "Please correct the errors below.")
            else:
                system_settings.save()
                success = True
                messages.success(request, "System settings updated successfully.")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        # Handle the response based on errors or success
        if errors:
            return render(
                request,
                "Admin/System_Settings.html",
                {
                    "system_settings": system_settings,
                    "MEDIA_URL": settings.MEDIA_URL,
                    "breadcrumb": {"parent": "Admin", "child": "System Settings"},
                    "errors": errors,
                },
            )
        elif success:
            return redirect("System_Settings")
        else:
            return redirect("System_Settings")



#######################################   Player Coach And Refree LIST VIEW MODULE ##############################################

# User Active & Deactive Function
@method_decorator(user_role_check, name='dispatch')
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
        elif source_page == "default_user_list":
            return redirect(reverse("default_user_list"))
        else:
            return redirect(reverse("Dashboard"))


# Player List View
@method_decorator(user_role_check, name='dispatch')
class PlayerListView(LoginRequiredMixin, View):
    template_name = "Admin/User/Player_List.html"

    def get(self, request):
        User = get_user_model()  # Get the custom user model
        users = User.objects.filter(role_id=2)  
        roles = Role.objects.filter(id=2)
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
@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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


# Default User List View
@method_decorator(user_role_check, name='dispatch')
class DefaultUserList(LoginRequiredMixin, View):
    template_name = "Admin/User/Default_User_List.html"

    def get(self, request):
        User = get_user_model()  # Get the custom user model
        users = User.objects.filter(role_id=5)  
        roles = Role.objects.filter(id=5)
        return render(
            request,
            self.template_name,
            {
                "users": users,
                "roles": roles,
                "breadcrumb": {"child": "Default User List"},
            },
        )


@method_decorator(user_role_check, name='dispatch')
class UserDetailView(LoginRequiredMixin, View):
    template_name = "Admin/User/User_Detail.html"
    
    def get_user_related_data(self, user):
        posts = Post.objects.filter(created_by_id=user.id, creator_type=Post.USER_TYPE)
        events = Event.objects.filter(event_organizer=user)
        event_bookings = EventBooking.objects.filter(created_by_id=user.id, creator_type=EventBooking.USER_TYPE)
        teams = JoinBranch.objects.filter(user_id=user.id)
        return posts, events, event_bookings, teams

    def get(self, request):
        user_id = request.GET.get('user_id') 
        if not user_id:
            return redirect('Dashboard') 
        try:
            user = User.objects.get(id=user_id)
            posts, events, event_bookings, teams = self.get_user_related_data(user)
            source_page = request.GET.get("source_page")
            title = request.GET.get("title")
            role = user.role_id  

            return render(
                request,
                self.template_name,
                {
                    "user": user,
                    "role": role,
                    "title": title,
                    "source_page": source_page,
                    "posts": posts,
                    "events": events,
                    "events_bookings": event_bookings, 
                    "teams": teams,
                },
            )
        except User.DoesNotExist:
            return redirect('Dashboard')  

    def post(self, request):
        user_id = request.POST.get('user_id')
        if not user_id:
            return redirect('Dashboard')  
        try:
            user = User.objects.get(id=user_id)
            posts, events, event_bookings, teams = self.get_user_related_data(user)
            source_page = request.POST.get("source_page")
            title = request.POST.get("title")
            role = user.role_id  

            return render(
                request,
                self.template_name,
                {
                    "user": user,
                    "role": role,
                    "title": title,
                    "source_page": source_page,
                    "posts": posts,  
                    "events": events,
                    "events_bookings": event_bookings, 
                    "teams": teams,
                },
            )
        except User.DoesNotExist:
            return redirect('Dashboard') 
 
        
##############################################  User Category Type Module  ################################################
# Category CRUD Views
@method_decorator(user_role_check, name='dispatch')
class CategoryCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = CategoryForm()
        return render(request, "forms/category_form.html", {"form": form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            # Check for existing category with the same name
            #changes will be done on server by this side 
            name_en = form.cleaned_data.get("name_en")
            if Category.objects.filter(name_en=name_en).exists():
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class NewsDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.delete()
        messages.success(request, "News Deleted Successfully.")
        return redirect("news_list")


############################################################## Partners Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class PartnersDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        partners = get_object_or_404(Partners, pk=pk)
        partners.delete()
        messages.success(request, "Partners Deleted Successfully.")
        return redirect("partners_list")


############################################################ Global Clients Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class Global_ClientsDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        global_clients = get_object_or_404(Global_Clients, pk=pk)
        global_clients.delete()
        messages.success(request, "Global Client Deleted Successfully.")
        return redirect("global_clients_list")


################################################################# Tryout Club Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class Tryout_ClubDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tryout_club = get_object_or_404(Tryout_Club, pk=pk)
        tryout_club.delete()
        messages.success(request, "Tryout Club Deleted Successfully.")
        return redirect("tryout_club_list")


#################################################################### Inquires Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class TestimonialDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        testimonial = get_object_or_404(Testimonial, pk=pk)
        testimonial.delete()
        messages.success(request, "Testimonial Deleted Successfully.")
        return redirect("testimonial_list")


################################################################ Team_Members Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class Team_MembersDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        team_members = get_object_or_404(Team_Members, pk=pk)
        team_members.delete()
        messages.success(request, "Team Member Deleted Successfully.")
        return redirect("team_members_list")


################################################################ App_Feature Module ###############################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
class App_FeatureDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        app_feature = get_object_or_404(App_Feature, pk=pk)
        app_feature.delete()
        messages.success(request, "App Feature Deleted Successfully.")
        return redirect("app_feature_list")


#################################################   Slider_Content CRUD Views  #######################################################
@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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

@method_decorator(user_role_check, name='dispatch')
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
@method_decorator(user_role_check, name='dispatch')      
class CMSPages(LoginRequiredMixin, View):
    template_name = "Admin/cmspages.html"
    

    def get(self,request):
        
        cms_pages_name = cms_pages.objects.all()
        
        context = {
            'cms_pages_name': cms_pages_name
        }
        
        
        return render(request, self.template_name,context)
    
 
 
 

 
######################################## cms_contact_page  ############################################################## 
@method_decorator(user_role_check, name='dispatch')     
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')     
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

@user_role_check     
@csrf_exempt
def saveAboutUspage(request):
        try:
            if request.method == "POST":
                #text
                heading_title_en  = request.POST.get('heading_title_en')
                heading_title_ar  = request.POST.get('heading_title_ar')
                heading_url = request.POST.get("heading_url")
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
                    aboutussave.heading_title_ar = heading_title_ar
                    aboutussave.heading_url = heading_url
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
@method_decorator(user_role_check, name='dispatch')
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')    
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')     
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')
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
@user_role_check
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
@method_decorator(user_role_check, name='dispatch')
class cms_discoverypage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/discovery.html"
    def get(self, request):
        try:
            whodetail= cms_dicovery_dynamic_view.objects.all()
            game_image = cms_dicovery_dynamic_image.objects.all()
        except Exception as e:
            with open("error.txt", "w") as f:
                f.write(str(e))
        dataFilter = cms_pages.objects.get(id='2')

        context = {
            'data':dataFilter, 
            'who_detail':whodetail,
            'game_image':game_image,
            
        }
        return render(
            request,
            self.template_name,
            context
            
    )  
        
#cms discover

    
    #discover page
    #cms discover
@csrf_exempt
@user_role_check
def saveDiscoverdetail(request):
        try:
            if request.method == "POST":
                #text
                try:
                    discover_heading_title_en = request.POST.get('discover_heading_title_en')
                    discover_heading_title_ar = request.POST.get('discover_heading_title_ar')
                    discover_title_en = request.POST.get('discover_title_en')
                    discover_title_ar = request.POST.get('discover_title_ar')
                    discover_content_en = request.POST.get('discover_content_en')
                    discover_content_ar = request.POST.get('discover_content_ar')
                    discover_game_title_en = request.POST.get('discover_game_title_en')
                    discover_game_title_ar = request.POST.get('discover_game_title_ar')
                    discover_game_content_en = request.POST.get('discover_game_content_en')
                    discover_game_content_ar = request.POST.get('discover_game_content_ar')
                    discover_training_heading_en = request.POST.get('training_section_1_heading_en')
                    discover_training_heading_ar = request.POST.get('training_section_1_heading_ar')
                    discover_training_sec_1_title_en = request.POST.get('discover_training_sec_1_title_en')
                    discover_training_sec_1_title_ar = request.POST.get('discover_training_sec_1_title_ar')
                    discover_training_sec_1_content_en = request.POST.get('discover_training_sec_1_content_en')
                    discover_training_sec_1_content_ar = request.POST.get('discover_training_sec_1_content_ar')
                    discover_training_sec_2_title_en = request.POST.get('discover_training_sec_2_title_en')
                    discover_training_sec_2_title_ar = request.POST.get('discover_training_sec_2_title_ar')
                    discover_training_sec_2_content_en = request.POST.get('discover_training_sec_2_content_en')
                    discover_training_sec_2_content_ar = request.POST.get('discover_training_sec_2_content_ar')
                    why_Choose_us_heading_en = request.POST.get('why_Choose_us_heading_en')
                    why_Choose_us_heading_ar = request.POST.get('why_Choose_us_heading_ar')
                    why_Choose_us_title_en = request.POST.get('why_Choose_us_title_en')
                    why_Choose_us_title_ar = request.POST.get('why_Choose_us_title_ar')
                    why_Choose_us_form_title_en = request.POST.get('why_Choose_us_form_title_en')
                    why_Choose_us_form_title_ar = request.POST.get('why_Choose_us_form_title_ar')

                    why_Choose_us_form_content_en = request.POST.get('why_Choose_us_form_content_en')
                    why_Choose_us_form_content_ar = request.POST.get('why_Choose_us_form_content_ar')
                    seo_title_en = request.POST.get('seo_title_en')
                    seo_title_ar = request.POST.get('seo_title_ar')
                    seo_content_en = request.POST.get('seo_content_en')
                    seo_content_ar = request.POST.get('seo_content_ar')
                    

                    try:
                   
                        discover_page  = cms_pages.objects.get(id='2')
                        
                        discover_page.heading_en = discover_heading_title_en
                        discover_page.heading_ar = discover_heading_title_ar
                        discover_page.heading_title_en =discover_title_en
                        discover_page.heading_title_ar =discover_title_ar
                        discover_page.heading_content_en = discover_content_en
                        discover_page.heading_content_ar = discover_content_ar
                        discover_page.section_2_title_en = discover_game_title_en
                        discover_page.section_2_title_ar = discover_game_title_ar
                        discover_page.section_2_content_en = discover_game_content_en
                        discover_page.section_2_content_ar = discover_game_content_ar
                        
                        discover_page.section_2_heading_en = discover_training_heading_en 
                        discover_page.section_2_heading_ar = discover_training_heading_ar


                        discover_page.section_2_discover_title_en  = discover_training_sec_1_title_en
                        discover_page.section_2_discover_title_ar = discover_training_sec_1_title_ar
                        discover_page.sub_section_2_content_1_en = discover_training_sec_1_content_en 
                        discover_page.sub_section_2_content_1_ar = discover_training_sec_1_content_ar 
                        discover_page.sub_section_2_title_2_en  = discover_training_sec_2_title_en 
                        discover_page.sub_section_2_title_2_ar  = discover_training_sec_2_title_ar 
                        discover_page.sub_section_2_content_2_en = discover_training_sec_2_content_en 
                        discover_page.sub_section_2_content_2_ar = discover_training_sec_2_content_ar 
                        discover_page.section_3_heading_en = why_Choose_us_heading_en 
                        discover_page.section_3_heading_ar = why_Choose_us_heading_ar 
                        discover_page.section_3_title_en = why_Choose_us_title_en 
                        discover_page.section_3_title_ar = why_Choose_us_title_ar 
                        discover_page.section_3_sub_title_en = why_Choose_us_form_title_en
                        discover_page.section_3_sub_title_ar = why_Choose_us_form_title_ar
                        discover_page.section_3_sub_content_en = why_Choose_us_form_content_en 
                        discover_page.section_3_sub_content_ar = why_Choose_us_form_content_ar 
                        discover_page.meta_title_en = seo_title_en
                        discover_page.meta_title_ar = seo_title_ar
                        discover_page.meta_content_en = seo_content_en
                        discover_page.meta_content_ar = seo_content_ar


                        who_count = request.POST.get('who_passed')
                        if who_count:
                            who_deleted_field = request.POST.get('deleted_who_field')

                            print(who_deleted_field)
                            
                            if 'deleted_who_field' in request.POST:
                                print("yes")
                                if ',' in who_deleted_field:
                                    deleted_who_list = who_deleted_field.split(',')
                                else:
                                    deleted_who_list = ['{}'.format(who_deleted_field)]  # Treat single value as list
                                    deleted_who_list = [int(item) for item in deleted_who_list]

                            else:
                                print("no")
                                deleted_who_list = []
                            # Convert strings to integers

                            print(deleted_who_list)
                                    

                            print("this is whoCount: "+str(who_count))
                            for i in range(2,int(who_count)+1):
                                
                                if str(i) in deleted_who_list:
                                    print("its in field ",i)
                                else:
                                    '''if 'field-roll-image-id-{}'.format(i) in request.POST: 
                                        unique_id = request.POST.get('ugid_{}'.format(i))
                                    
                                        print("exisiting: "+str(existing_record))'''
                                                
    
                                        
                                    unique_id = request.POST.get('uwid_{}'.format(i))
                                    if unique_id != "":
                                    
                                        who_title_en = request.POST.get('why_choose_us_heading_title_en_{}'.format(str(i)))
                                        who_title_ar = request.POST.get('why_choose_us_heading_title_ar_{}'.format(str(i)))
                                        who_content_en = request.POST.get('why_choose_us_content_en_{}'.format(str(i)))
                                        who_content_ar = request.POST.get('why_choose_us_content_ar_{}'.format(str(i)))
                                        existing_who_record = cms_dicovery_dynamic_view.objects.filter(field_id=unique_id).first()


                                                    
                                                
                                        
                                        if existing_who_record:
                                                        # Update the existing record
                                                        
                                                        
                                                            existing_who_record.title_en = who_title_en
                                                            existing_who_record.title_ar = who_title_ar
                                                            existing_who_record.content_en = who_content_en
                                                            existing_who_record.content_ar = who_content_ar
                                                                    
                                                            
                                                            existing_who_record.save() 
                                        else:        
                                                        savediscoveryview= cms_dicovery_dynamic_view(
                                                                    field_id=unique_id,
                                                                    title_en=who_title_en,
                                                                    title_ar=who_title_ar,
                                                                    content_en=who_content_en,
                                                                    content_ar=who_content_ar,
                                                                
                                                                    
                                                        )
                                                        savediscoveryview.save()
                                                    
                                                    
                        '''if who_count:
                                for i in range(int(who_count)+1):
                                    print("loop calue:"+str(i))
                                    dom = i+2
                                    print("loop: "+str(dom))
                                    who_title_en = request.POST.get('why_choose_us_heading_title_en_{}'.format(str(dom)))
                                    who_title_ar = request.POST.get('why_choose_us_heading_title_ar_{}'.format(str(dom)))
                                    who_content_en = request.POST.get('why_choose_us_content_en_{}'.format(str(dom)))
                                    who_content_ar = request.POST.get('why_choose_us_content_ar_{}'.format(str(dom)))
                                    unique_id = request.POST.get('uwid_{}'.format(dom))
                                    
                                    print("title_ar {}: ".format(dom)+str(who_title_en))
                                    print("USER_Id: ",unique_id)
                                    existing_who_record = cms_dicovery_dynamic_view.objects.filter(field_id=unique_id).first()
                                    print("exisiting: "+str(existing_who_record))
                                    
                                
                                    if existing_who_record:
                                            # Update the existing record
                                            existing_who_record.title_en = who_title_en
                                            existing_who_record.title_ar = who_title_ar
                                            existing_who_record.content_en = who_content_en
                                            existing_who_record.content_ar = who_content_ar
                                            
                                            
                                            existing_who_record.save()  # Save the updated record
                                            print("exsiting_title: "+str(existing_who_record.title_en))
                                            
                                    else:        
                                        savediscoverdynamcidetail = cms_dicovery_dynamic_view(
                                                    field_id=unique_id,
                                                    title_en=who_title_en,
                                                    title_ar=who_title_ar,
                                                    content_en=who_content_en,
                                                    content_ar=who_content_ar,
                                        )
                                        savediscoverdynamcidetail.save()    
                                        with open("hell.txt","a") as f:
                                            f.write(str(who_title_en)+" ")    
                                        
                                        print("last unique id: "+str(unique_id))
                                    #delete_record = cms_home_dynamic_field.objects.filter(field_id = None)
                                    #delete_record.delete()'''

                                
                        game_image = request.POST.get('header_image')
                        
                        if game_image:
                            image_deleted_field = request.POST.get('deleted_image_field')

                            if 'deleted_image_field' in request.POST:
                                print("yes")
                                if ',' in image_deleted_field:
                                    deleted_image_list = image_deleted_field.split(',')
                                else:
                                    deleted_image_list = [image_deleted_field]  # Treat single value as list
                                    deleted_image_list = [int(item) for item in deleted_image_list]

                            else:
                                print("no")
                                deleted_image_list = []
                            # Convert strings to integers

                            print(deleted_image_list)
                                    
                            print("this is game imgaes: "+str(game_image))
                            
                            if game_image != None:
                                for i in range(2,int(game_image)+1):
                                    
                                    if i in deleted_image_list:
                                        print("its in field ",i)
                                    else:
                                        '''if 'field-roll-image-id-{}'.format(i) in request.POST: 
                                            unique_id = request.POST.get('ugid_{}'.format(i))
                                        
                                            print("exisiting: "+str(existing_record))'''
                                                    
        
                                        if 'image_{}'.format(str(i)) in request.FILES:
                                            
                                                    unique_id = request.POST.get('ugid_{}'.format(i))
                                                    existing_record = cms_dicovery_dynamic_image.objects.filter(field_id=unique_id).first()


                                                    image = request.FILES.get('image_{}'.format(str(i)),None)
                                                    
                                                    if image:
                                                        try:
                                                            save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                                            os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                            # Save the file
                                                            with open(save_path, 'wb+') as destination:
                                                                for chunk in image.chunks():
                                                                    destination.write(chunk)
                                                                    #imageName.append(heading_banner.name)
                                                                    #savenewsdetail.heading_banner = heading_banner

                                                        except Exception as e:
                                                            dom = str(e)
                                        
                                                    if existing_record:
                                                        # Update the existing record
                                                        
                                                        
                                                        if image:  # Update the image if a new one is uploaded
                                                            existing_record.images = image

                                                        existing_record.save()  # Save the updated record
                                                    else:        
                                                        savediscoveryimage_view= cms_dicovery_dynamic_image(
                                                                    field_id=unique_id,
                                                                
                                                                    images=image
                                                        )
                                                        savediscoveryimage_view.save()
                                                    
                        '''if game_image:
                            for i in range(2,int(game_image)+1):
                                        
                                        #dom = i+1
                                        #image = 0
                                        #print("loop: "+str(dom))
                
                                        unique_id = request.POST.get('ugid_{}'.format(i))
                                        print(unique_id)
                                        
                                        existing_record = cms_dicovery_dynamic_image.objects.filter(field_id=unique_id).first()
                                        print("exisiting: "+str(existing_record))
                                        
                                        if 'image_{}'.format(str(i)) in request.FILES:
                                            print("yes")
                                            image = request.FILES.get('image_{}'.format(str(i)),None)
                                            
                                            if image:
                                                try:
                                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                    # Save the file
                                                    with open(save_path, 'wb+') as destination:
                                                        for chunk in image.chunks():
                                                            destination.write(chunk)
                                                            #imageName.append(heading_banner.name)
                                                            #savenewsdetail.heading_banner = heading_banner

                                                except Exception as e:
                                                    dom = str(e)
                                            
                                        if existing_record:
                                                # Update the existing record
                                                
                                                
                                                if image:  # Update the image if a new one is uploaded
                                                    existing_record.images = image

                                                existing_record.save()  # Save the updated record
                                        else:        
                                            savediscoveryimage_view= cms_dicovery_dynamic_image(
                                                        field_id=unique_id,
                                                       
                                                        images=image
                                            )
                                            savediscoveryimage_view.save()'''
                        if 'discovery_game_image' in request.FILES:
                            print("yes")
                            
                            
                            game_image = request.FILES.get('discovery_game_image',None)
                            
                            if game_image:
                                try:
                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', game_image.name)
                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                    # Save the file
                                    with open(save_path, 'wb+') as destination:
                                        for chunk in game_image.chunks():
                                            destination.write(chunk)
                                            #imageName.append(heading_banner.name)
                                            discover_page.section_2_images = game_image
                                            print("image_saved")

                                except Exception as e:
                                        messages.error(request,str(e))    

                        else:
                            pass  
                        
                        if 'discover_heading_image' in request.FILES:
                            print("hdeaing banner")
                            
                            
                            heading_image = request.FILES.get('discover_heading_image',None)
                            print(heading_image)
                            if heading_image:
                                try:
                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', heading_image.name)
                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                    # Save the file
                                    with open(save_path, 'wb+') as destination:
                                        for chunk in heading_image.chunks():
                                            destination.write(chunk)
                                            #imageName.append(heading_banner.name)
                                            discover_page.heading_banner = heading_image
                                            print("image_saved")

                                except Exception as e:
                                        messages.error(request,str(e))    

                        else:
                            pass  
                       
                        if 'discover_training_sec_1_image_field' in request.FILES:
                            print("yes")
                            
                            
                            training_1_image = request.FILES.get('discover_training_sec_1_image_field',None)
                            
                            if training_1_image:
                                try:
                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', training_1_image.name)
                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                    # Save the file
                                    with open(save_path, 'wb+') as destination:
                                        for chunk in training_1_image.chunks():
                                            destination.write(chunk)
                                            #imageName.append(heading_banner.name)
                                            discover_page.sub_section_2_1_icon = training_1_image 
                                            print("image_saved")

                                except Exception as e:
                                        messages.error(request,str(e))    

                        else:
                            pass 
                        
                        if 'discover_training_sec_2_image_field' in request.FILES:
                            print("yes")
                            
                            
                            training_2_image = request.FILES.get('discover_training_sec_2_image_field',None)
                            
                            if training_2_image:
                                try:
                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', training_2_image.name)
                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                    # Save the file
                                    with open(save_path, 'wb+') as destination:
                                        for chunk in training_2_image.chunks():
                                            destination.write(chunk)
                                            #imageName.append(heading_banner.name)
                                            discover_page.sub_section_2_2_icon = training_2_image
                                            print("image_saved")

                                except Exception as e:
                                        messages.error(request,str(e))    

                        else:
                            pass 
                        
                        if 'why_Choose_us_image_field' in request.FILES:
                            print("yes")
                            
                            
                            who_image = request.FILES.get('why_Choose_us_image_field',None)
                            
                            if who_image:
                                try:
                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', who_image.name)
                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                    # Save the file
                                    with open(save_path, 'wb+') as destination:
                                        for chunk in who_image.chunks():
                                            destination.write(chunk)
                                            #imageName.append(heading_banner.name)
                                            discover_page.section_3_image = who_image
                                            print("image_saved")

                                except Exception as e:
                                        messages.error(request,str(e))    

                        else:
                            pass 
                                        
                        discover_page.save()
                        
                        
                        if "dyanmic_deleted_field" in request.POST:
                            
                            try:
                                dynamic_data = request.POST.get('dyanmic_deleted_field')
                                dynamic_deleted_list = dynamic_data.split(',')
                                print(dynamic_deleted_list)
                                
                                for i in range(len(dynamic_deleted_list)):
                                    
                                    
                                    deletingimagefrom_data = cms_dicovery_dynamic_image.objects.filter(field_id = dynamic_deleted_list[i]).delete()

                                
                            except Exception as e:
                                print(e)    

                                messages.error(request, str(e))
                        
                        if "dyanmic_deleted_who_field" in request.POST:
                            
                            try:
                                dynamic_who_data = request.POST.get('dyanmic_deleted_who_field')
                                dynamic_deleted_who_list = dynamic_who_data.split(',')
                                print(dynamic_deleted_who_list)
                                
                                for i in range(len(dynamic_deleted_who_list)):
                                    
                                    
                                    deletingviewfrom_data = cms_dicovery_dynamic_view.objects.filter(field_id = dynamic_deleted_who_list[i]).delete()

                                
                            except Exception as e:
                                print(e)    

                                messages.error(request, str(e))        

                    
                        messages.success(request, "Discovery Page Updated Successfully")
                        
                        
                    except Exception as e:
                        print(sys.exc_info)
                        print(str(e))
                        messages.error(request,str(e))    
                        

                except Exception as e:
                    print(str(e))
                    print(sys.exc_info)

                    messages.error(request,str(e))    
                

                               
                
              
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
            
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
        
    
#cms Advertise page
@method_decorator(user_role_check, name='dispatch')
class cms_advertisepage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/advertise.html"
    
    def get(self, request):
        dataFilter = cms_pages.objects.get(id="6")
        section_2_data = cms_advertise_section_2_dynamic_field.objects.all()
        partnership_data = cms_advertise_Partnership_dynamic_field.objects.all()
        ads = cms_advertise_ads_dynamic_field.objects.all()
        premium = cms_advertise_premium_dynamic_field.objects.all()
        context = {
            'data':dataFilter,
            'section_2':section_2_data,
            'partnership':partnership_data,
            'ads':ads,
            'premium':premium,
        }
        return render(
            request,
            self.template_name,
            context
            
    )     
#cms advertise
@user_role_check
@csrf_exempt
def saveadvertisedetail(request):
        try:
            if request.method == "POST":
                #text
                
                heading_title_en = request.POST.get('advertise-heading-title-en')
                heading_title_ar = request.POST.get('advertise-heading-title-ar')
                heading_content_en = request.POST.get('advertise-heading-content-en')
                heading_content_ar = request.POST.get('advertise-heading-content-ar')
                section_2_title_en = request.POST.get('section-2-title-en')
                section_2_title_ar = request.POST.get('section-2-title-ar')
                section_2_content_en = request.POST.get('section-2-content-en')
                section_2_content_ar = request.POST.get('section-2-content-ar')
                
                partnership_heading_name_en_1 = request.POST.get('partnership_heading_name_en_1')
                partnership_heading_name_ar_1 = request.POST.get('partnership_heading_name_ar_1')
                print("heading: ",partnership_heading_name_ar_1)

                partnership_heading_title_en_1 = request.POST.get('partnership-heading-title-en-1')
                partnership_heading_title_ar_1 = request.POST.get('partnership-heading-title-ar-1')
                partnership_title_en = request.POST.get('partnership-title-en')
                partnership_title_ar = request.POST.get('partnership-title-ar')
                partnership_content_en = request.POST.get('partnership_content_en')
                partnership_content_ar = request.POST.get('partnership_content_ar')


                ads_heading_name_en = request.POST.get('ads-heading-name-en')
                ads_heading_name_ar = request.POST.get('ads-heading-name-ar')
                ads_heading_title_en = request.POST.get('ads-heading-title-en')
                ads_heading_title_ar = request.POST.get('ads-heading-title-ar')


                
                
                premium_title_en = request.POST.get('premium-title-en')
                premium_title_ar= request.POST.get('premium-title-ar')
                premium_title_en_1 = request.POST.get('premium-title-en-1')
                premium_title_ar_1 = request.POST.get('premium-title-ar-1')
                
                social_media_title_en = request.POST.get('social-media-title-en')
                social_media_title_ar = request.POST.get('social-media-title-ar')
                
                social_media_content_en_1 = request.POST.get('social-media-content-en-1')
                social_media_content_ar_1 = request.POST.get('social-media-content-ar-1')
                social_media_content_en_2 = request.POST.get('social-media-content-en-2')
                social_media_content_ar_2 = request.POST.get('social-media-content-ar-2')
                social_media_content_en_3 = request.POST.get('social-media-content-en-3')
                social_media_content_ar_3 = request.POST.get('social-media-content-ar-3')
                social_media_content_en_4 = request.POST.get('social-media-content-en-4')
                social_media_content_ar_4 = request.POST.get('social-media-content-ar-4')
                social_media_content_en_5 = request.POST.get('social-media-content-en-5')
                social_media_content_ar_5 = request.POST.get('social-media-content-ar-5')
                social_media_content_en_6 = request.POST.get('social-media-content-en-6')
                social_media_content_ar_6 = request.POST.get('social-media-content-ar-6')

                competition_section_title_en = request.POST.get('competition-section-title-en')
                competition_section_title_ar = request.POST.get('competition-section-title-ar')
                competition_section_content_en= request.POST.get('competition-section-content-en')
                competition_section_content_ar = request.POST.get('competition-section-content-ar')


                seo_title_en = request.POST.get('seo-title-en')
                seo_title_ar = request.POST.get('seo-title-ar')
                seo_content_en = request.POST.get('seo-content-en')
                seo_content_ar = request.POST.get('seo-content-ar')
                
              
                #imageName = []
                
                try:
                    #savenewsdetail = cms_pages.objects.get(id = "5")
                    
                    saveadvertiseetail = cms_pages.objects.get(id="6")

                    saveadvertiseetail.heading_title_en = heading_title_en
                    saveadvertiseetail.heading_title_ar = heading_title_ar
                    saveadvertiseetail.heading_content_en = heading_content_en
                    saveadvertiseetail.heading_content_ar = heading_content_ar
                    
                    saveadvertiseetail.section_2_title_en = section_2_title_en
                    saveadvertiseetail.section_2_title_ar = section_2_title_ar
                    
                    print("advertise: "+str(section_2_title_ar))
                    saveadvertiseetail.section_2_content_en = section_2_content_en
                    saveadvertiseetail.section_2_content_ar = section_2_content_ar
                    
                    saveadvertiseetail.section_3_heading_en = partnership_heading_name_en_1
                    saveadvertiseetail.section_3_heading_ar = partnership_heading_name_ar_1
                    saveadvertiseetail.section_3_titlee_en = partnership_heading_title_en_1
                    saveadvertiseetail.section_3_titlee_ar = partnership_heading_title_ar_1
                    saveadvertiseetail.section_3_title_en = partnership_title_en
                    saveadvertiseetail.section_3_title_ar = partnership_title_ar
                    saveadvertiseetail.section_3_content_en = partnership_content_en
                    saveadvertiseetail.section_3_content_ar = partnership_content_ar

                    saveadvertiseetail.section_4_heading_en = ads_heading_name_en
                    saveadvertiseetail.section_4_heading_ar = ads_heading_name_ar
                    saveadvertiseetail.section_4_title_en = ads_heading_title_en
                    saveadvertiseetail.section_4_title_ar = ads_heading_title_ar
              

                    saveadvertiseetail.section_5_heading_en = premium_title_en
                    saveadvertiseetail.section_5_heading_ar = premium_title_ar
                    saveadvertiseetail.section_5_title_en = premium_title_en_1
                    saveadvertiseetail.section_5_title_ar = premium_title_ar_1
                    
                    saveadvertiseetail.section_6_title_en = social_media_title_en
                    saveadvertiseetail.section_6_title_ar = social_media_title_ar

                    saveadvertiseetail.section_6_content_1_en = social_media_content_en_1
                    saveadvertiseetail.section_6_content_1_ar = social_media_content_ar_1
                    saveadvertiseetail.section_6_content_2_en = social_media_content_en_2
                    saveadvertiseetail.section_6_content_2_ar = social_media_content_ar_2
                    saveadvertiseetail.section_6_content_3_en = social_media_content_en_3
                    saveadvertiseetail.section_6_content_3_ar = social_media_content_ar_3
                    saveadvertiseetail.section_6_content_4_en = social_media_content_en_4
                    saveadvertiseetail.section_6_content_4_ar = social_media_content_ar_4
                    saveadvertiseetail.section_6_content_5_en = social_media_content_en_5
                    saveadvertiseetail.section_6_content_5_ar= social_media_content_ar_5
                    saveadvertiseetail.section_6_content_6_en= social_media_content_en_6
                    saveadvertiseetail.section_6_content_6_ar= social_media_content_ar_6
                    
                    saveadvertiseetail.section_9_heading_en = competition_section_title_en
                    saveadvertiseetail.section_9_heading_ar = competition_section_title_ar
                    saveadvertiseetail.section_9_title_en = competition_section_content_en
                    saveadvertiseetail.section_9_title_ar = competition_section_content_ar

                    saveadvertiseetail.meta_title_en  = seo_title_en
                    saveadvertiseetail.meta_title_ar  = seo_title_ar
                    saveadvertiseetail.meta_content_en  = seo_content_en
                    saveadvertiseetail.meta_content_ar   = seo_content_ar
                    '''if 'heading_banner' in request.FILES:
                        
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
                        pass'''
                    
                    '''savenewsdetail.section_2_title_en = heading_title_en
                    savenewsdetail.section_2_title_ar = heading_title_ar
                    savenewsdetail.section_2_content_en = heading_content_en
                    savenewsdetail.section_2_content_ar = heading_content_ar
                    savenewsdetail.meta_title_en = seo_title_en
                    savenewsdetail.meta_title_ar = seo_title_ar
                    savenewsdetail.meta_content_en = seo_content_en
                    savenewsdetail.meta_content_ar = seo_content_ar

                    savenewsdetail.save()'''
                    
                    
                    '''feature_count = request.POST.get('features_passed')
                    
                    print("this is feature: "+str(feature_count))
                    if feature_count:
                        for i in range(int(feature_count)+1):
                            
                            dom = i+1
                            image = 0
                            print("loop: "+str(dom))
                            feature_title_en = request.POST.get('features_section_form_title_en_{}'.format(str(dom)))
                            feature_title_ar = request.POST.get('features_section_form_title_ar_{}'.format(str(dom)))
                            feature_content_en = request.POST.get('features_section_form_content_en_{}'.format(str(dom)))
                            feature_content_ar = request.POST.get('features_section_form_content_ar_{}'.format(str(dom)))
                            feature_field = request.POST.get('id')
                            unique_id = request.POST.get('uid_{}'.format(dom))
                            print(unique_id)
                            print("title_ar {}: ".format(dom)+str(feature_title_ar))
                            
                            existing_record = cms_home_dynamic_field.objects.filter(field_id=unique_id).first()
                            print("exisiting: "+str(existing_record))
                            
                            if 'image_{}'.format(str(dom)) in request.FILES:
                                
                                image = request.FILES.get('image_{}'.format(str(dom)),None)
                                print("image: "+str(image))
                                
                                if image:
                                    try:
                                        save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                        # Save the file
                                        with open(save_path, 'wb+') as destination:
                                            for chunk in image.chunks():
                                                destination.write(chunk)
                                                #imageName.append(heading_banner.name)
                                                #savenewsdetail.heading_banner = heading_banner

                                    except Exception as e:
                                        dom = str(e)
                                
                            if existing_record:
                                    # Update the existing record
                                    existing_record.title_en = feature_title_en
                                    existing_record.title_ar = feature_title_ar
                                    existing_record.content_en = feature_content_en
                                    existing_record.content_ar = feature_content_ar
                                    
                                    if image:  # Update the image if a new one is uploaded
                                        existing_record.images = image

                                    existing_record.save()  # Save the updated record
                                    print("exsiting_title: "+str(existing_record.title_en))
                            else:        
                                savehomedynamcidetail = cms_home_dynamic_field(
                                            field_id=unique_id,
                                            title_en=feature_title_en,
                                            title_ar=feature_title_ar,
                                            content_en=feature_content_en,
                                            content_ar=feature_content_ar,
                                            images=image
                                )
                                savehomedynamcidetail.save()        
                                
                                print("last unique id: "+str(unique_id))
                            delete_record = cms_home_dynamic_field.objects.filter(field_id = None)
                            delete_record.delete()
                            
                             #achivement section
                        

                        
                            #savehomedynamcidetail.save() 
                            print("this is id: "+feature_field)
                            if 'image_{}'.format(str(dom)) in request.FILES:
                                
                                image = request.FILES.get('image_{}'.format(str(dom)),None)
                                print("image: "+str(image))
                                
                                if image:
                                    try:
                                        save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                        # Save the file
                                        with open(save_path, 'wb+') as destination:
                                            for chunk in image.chunks():
                                                destination.write(chunk)
                                                #imageName.append(heading_banner.name)
                                                #savenewsdetail.heading_banner = heading_banner

                                    except Exception as e:
                                        dom = str(e)
                                
                                #savehomedynamcidetail = cms_home_dynamic_field(field_id = feature_field,title_en =feature_title_en,title_ar = feature_title_ar,content_en=feature_content_en,content_ar = feature_content_ar,images = image)
                            existing_record = cms_home_dynamic_field.objects.filter(field_id=feature_field).first()
                            print("exisiting: "+str(existing_record))
                            if existing_record:
                                    # Update the existing record
                                    existing_record.title_en = feature_title_en
                                    existing_record.title_ar = feature_title_ar
                                    existing_record.content_en = feature_content_en
                                    existing_record.content_ar = feature_content_ar
                                    
                                    if image:  # Update the image if a new one is uploaded
                                        existing_record.images = image

                                    existing_record.save()  # Save the updated record
                                    print(existing_record.title_en)
                            else:
                                    # Create a new record if one doesn't exist
                                    savehomedynamcidetail = cms_home_dynamic_field(
                                        field_id=feature_field,
                                        title_en=feature_title_en,
                                        title_ar=feature_title_ar,
                                        content_en=feature_content_en,
                                        content_ar=feature_content_ar,
                                        images=image
                                    )
                                    savehomedynamcidetail.save() 
                                #savehomedynamcidetail.save()     
                        else:
                                pass 
                    savehomedetail.save()       ''' 
                    
                    '''deletedField = request.POST.get('deletedField')
                    print(deletedField)
                    
                    if deletedField !=0:
                        for i in range(int(deletedField)):
                            
                            deleted_id = request.POST.get('deleted_field_{}'.format(i))
                            print(deleted_id)
                            delete_the_record  = cms_home_dynamic_field.objects.filter(field_id = deleted_id ).delete()
                    else:
                        print("value is 0")''' 
                        
                    section_count = request.POST.get('section_field_passed')
                    print(section_count)
                    if section_count:
                        print("count is :"+str(section_count))
                        section_deleted_field = request.POST.get('deleteing_section2field')
                        print(section_deleted_field)
                            
                        if 'deleteing_section2field' in request.POST:
                                print("yes")
                                if ',' in section_deleted_field:
                                    deleted_section_list = section_deleted_field.split(',')
                                else:
                                    deleted_section_list = ['{}'.format(section_deleted_field)]  # Treat single value as list
                                    deleted_section_list = [int(item) for item in deleted_section_list]

                        else:
                                print("no")
                                deleted_section_list = []
                            # Convert strings to integers

                        print(deleted_section_list)
                                    

                        print("this is whoCount: "+str(section_count))
                        for i in range(2,int(section_count)+1):
                            
                                
                                if str(i) in deleted_section_list:
                                    print("its in field ",i)
                                else:
                                    '''if 'field-roll-image-id-{}'.format(i) in request.POST: 
                                        unique_id = request.POST.get('ugid_{}'.format(i))
                                    
                                        print("exisiting: "+str(existing_record))'''
                                                
    
                                        
                                    unique_id = request.POST.get('usid_{}'.format(i))
                                    if unique_id != "":
                                    
                                        section_title_en = request.POST.get('section_2_title_en_{}'.format(str(i)))
                                        section_title_ar = request.POST.get('section_2_title_ar_{}'.format(str(i)))
                                        section_content_en = request.POST.get('section_2_content_en_{}'.format(str(i)))
                                        section_content_ar = request.POST.get('section_2_content_ar_{}'.format(str(i)))
                                        existing_section_record = cms_advertise_section_2_dynamic_field.objects.filter(field_id=unique_id).first()

                                        print("Name: "+section_title_en)
                                        
                                        if 'imagess_{}'.format(str(i)) in request.FILES:
                                    
                                            image_1 = request.FILES.get('imagess_{}'.format(str(i)),None)
                                            print("image: "+str(image_1))
                                            
                                            if image_1:
                                                try:
                                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_1.name)
                                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                    # Save the file
                                                    with open(save_path, 'wb+') as destination:
                                                        for chunk in image_1.chunks():
                                                            destination.write(chunk)
                                                            #imageName.append(heading_banner.name)
                                                            #savenewsdetail.heading_banner = heading_banner

                                                except Exception as e:
                                                    dom = str(e)            
                                                
                                        
                                        if existing_section_record:
                                                        # Update the existing record
                                                        
                                                        
                                                            existing_section_record.title_en = section_title_en
                                                            existing_section_record.title_ar = section_title_ar
                                                            existing_section_record.content_en = section_content_en
                                                            existing_section_record.content_ar = section_content_ar
                                                            try:        
                                                                if image_1:
                                                                    existing_section_record.images = image_1
                                                            except Exception as e:
                                                                print(str(e))        
                                                                
                                                            existing_section_record.save() 
                                        else:        
                                                        savediscoveryview= cms_advertise_section_2_dynamic_field(
                                                                    field_id=unique_id,
                                                                    title_en=section_title_en,
                                                                    title_ar=section_title_ar,
                                                                    content_en=section_content_en,
                                                                    content_ar=section_content_ar,
                                                                    images = image_1
                                                                
                                                                    
                                                        )
                                                        savediscoveryview.save() 
                        
                    partnership_count = request.POST.get('partnership_field_passed')
                    print("partnership: ",partnership_count)
                    if partnership_count:
                        partnership_deleted_field = request.POST.get('deleteing_partnershipfield')
                        print(partnership_deleted_field)
                            
                        if 'partnership_deleted_field' in request.POST:
                                print("yes")
                                if ',' in partnership_deleted_field:
                                    deleted_partnership_list = partnership_deleted_field.split(',')
                                else:
                                    deleted_partnership_list = ['{}'.format(deleted_partnership_list)]  # Treat single value as list
                                    deleted_partnership_list = [int(item) for item in deleted_partnership_list]

                        else:
                                print("no")
                                deleted_partnership_list = []
                            # Convert strings to integers

                        print(deleted_partnership_list)
                                    

                        print("this is Partnerhsip : "+str(partnership_count))
                        for i in range(2,int(partnership_count)+1):
                            
                                
                                if str(i) in  deleted_partnership_list:
                                    print("its in field ",i)
                                else:
                                    '''if 'field-roll-image-id-{}'.format(i) in request.POST: 
                                        unique_id = request.POST.get('ugid_{}'.format(i))
                                    
                                        print("exisiting: "+str(existing_record))'''
                                                
    
                                        
                                    unique_id = request.POST.get('upid_{}'.format(i))
                                    if unique_id != "":
                                    
                                        partnership_title_en = request.POST.get('partnership_title_en_{}'.format(str(i)))
                                        partnership_title_ar = request.POST.get('partnership_title_ar_{}'.format(str(i)))
                                        partnership_content_en = request.POST.get('partnership_content_en_{}'.format(str(i)))
                                        partnership_content_ar = request.POST.get('partnership_content_ar_{}'.format(str(i)))
                                        existing_partnership_record = cms_advertise_Partnership_dynamic_field.objects.filter(field_id=unique_id).first()

                                        print(partnership_title_en)

                                        if 'imagep1p_{}'.format(str(i)) in request.FILES:
                                    
                                            image_2 = request.FILES.get('imagep1p_{}'.format(str(i)),None)
                                            print("image: "+str(image_2))
                                            
                                            if image_2:
                                                try:
                                                    save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_2.name)
                                                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                    # Save the file
                                                    with open(save_path, 'wb+') as destination:
                                                        for chunk in image_2.chunks():
                                                            destination.write(chunk)
                                                            #imageName.append(heading_banner.name)
                                                            #savenewsdetail.heading_banner = heading_banner

                                                except Exception as e:
                                                    dom = str(e)            
                                                
                                        
                                        if existing_partnership_record:
                                                        # Update the existing record
                                                        
                                                        
                                                            existing_partnership_record.title_en = partnership_title_en
                                                            existing_partnership_record.title_ar = partnership_title_ar
                                                            existing_partnership_record.content_en = partnership_content_en
                                                            existing_partnership_record.content_ar = partnership_content_ar
                                                            try:        
                                                                if image_2:
                                                                    existing_partnership_record.images = image_2
                                                            except Exception as e:
                                                                print(str(e))        
                                                                
                                                            existing_partnership_record.save() 
                                        else:        
                                                        savepdiscoveryview= cms_advertise_Partnership_dynamic_field(
                                                                    field_id=unique_id,
                                                                    title_en=partnership_title_en,
                                                                    title_ar=partnership_title_ar,
                                                                    content_en=partnership_content_en,
                                                                    content_ar=partnership_content_ar,
                                                                    images = image_2
                                                                
                                                                    
                                                        )
                                                        savepdiscoveryview.save()   
                    
                    ads_image = request.POST.get('ads_image')
                    
                    if ads_image:
                        image_deleted_field = request.POST.get('deleted_ads_field')
                            
                            
                        if 'deleted_ads_field' in request.POST:
                                print("yes")
                                if ',' in image_deleted_field:
                                    deleted_image_list = image_deleted_field.split(',')
                                else:
                                    deleted_image_list = [image_deleted_field]  # Treat single value as list
                                    deleted_image_list = [int(item) for item in deleted_image_list]

                        else:
                                print("no")
                                deleted_image_list = []
                            # Convert strings to integers

                        print(deleted_image_list)
                                    
                        print("this is game imgaes: "+str(ads_image))
                            
                        for i in range(2,int(ads_image)+1):
                                    
                                    if i in deleted_image_list:
                                        print("its in field ",i)
                                    else:
                                        '''if 'field-roll-image-id-{}'.format(i) in request.POST: 
                                            unique_id = request.POST.get('ugid_{}'.format(i))
                                        
                                            print("exisiting: "+str(existing_record))'''
                                                    
        
                                        if 'imageapp_{}'.format(str(i)) in request.FILES:
                                            
                                                    unique_id = request.POST.get('uaid_{}'.format(i))
                                                    existing_record = cms_advertise_ads_dynamic_field.objects.filter(field_id=unique_id).first()


                                                    image_3 = request.FILES.get('imageapp_{}'.format(str(i)),None)
                                                    
                                                    if image_3:
                                                        try:
                                                            save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_3.name)
                                                            os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                            # Save the file
                                                            with open(save_path, 'wb+') as destination:
                                                                for chunk in image_3.chunks():
                                                                    destination.write(chunk)
                                                                    #imageName.append(heading_banner.name)
                                                                    #savenewsdetail.heading_banner = heading_banner

                                                        except Exception as e:
                                                            dom = str(e)
                                        
                                                    if existing_record:
                                                        # Update the existing record
                                                        
                                                        try:
                                                            if image_3:  # Update the image if a new one is uploaded
                                                                existing_record.images = image_3
                                                        except Exception as e:
                                                            print(str(e))        

                                                        existing_record.save()  # Save the updated record
                                                    else:        
                                                        savediscoveryimage_view= cms_advertise_ads_dynamic_field(
                                                                    field_id=unique_id,
                                                                
                                                                    images=image_3
                                                        )
                                                        savediscoveryimage_view.save()                                                                       
                    premium_count = request.POST.get('premium_field_passed')
                    if premium_count:
                        premium_deleted_field = request.POST.get('deleteing_premium_field')
                        print(premium_deleted_field)
                        
                        if 'deleteing_premium_field' in request.POST:
                            print("yes")
                            if ',' in premium_deleted_field:
                                deleted_premium_list = premium_deleted_field.split(',')
                            else:
                                print("yes")
                                # Correct the variable reference here
                                deleted_premium_list = ['{}'.format(premium_deleted_field)]  # Treat single value as list
                            deleted_premium_list = [int(item) for item in deleted_premium_list]  # Convert to integers

                        else:
                            print("no")
                            deleted_premium_list = []

                        print(deleted_premium_list)

                        print("this is Premium: " + str(premium_count))
                        for i in range(2, int(premium_count) + 1):
                            if str(i) in deleted_premium_list:
                                print("its in field ", i)
                            else:
                                unique_id = request.POST.get('uppid_{}'.format(i))
                                print("advertise unique field: ",unique_id)
                                if unique_id != "":
                                    premium_title_en = request.POST.get('premium_title_en_{}'.format(str(i)))
                                    premium_title_ar = request.POST.get('premium_title_ar_{}'.format(str(i)))
                                    existing_premium_record = cms_advertise_premium_dynamic_field.objects.filter(field_id=unique_id).first()

                                    if 'imagepp_{}'.format(str(i)) in request.FILES:
                                        image_4 = request.FILES.get('imagepp_{}'.format(str(i)), None)
                                        print(image_4)
                                        print("image: " + str(image_4))
                                        if image_4:
                                            try:
                                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_4.name)
                                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                                # Save the file
                                                with open(save_path, 'wb+') as destination:
                                                    for chunk in image_4.chunks():
                                                        destination.write(chunk)

                                            except Exception as e:
                                                dom = str(e)

                                    if existing_premium_record:
                                        # Update the existing record
                                        existing_premium_record.title_en = premium_title_en
                                        existing_premium_record.title_ar = premium_title_ar
                                        try:
                                            if image_4:
                                                existing_premium_record.images = image_4
                                        except Exception as e:
                                            print(str(e))

                                        existing_premium_record.save()
                                    else:
                                        saveadvertiseview = cms_advertise_premium_dynamic_field(
                                            field_id=unique_id,
                                            title_en=premium_title_en,
                                            title_ar=premium_title_ar,
                                            images=image_4
                                        )
                                        saveadvertiseview.save()

                    if 'heading_image_1' in request.FILES:
                        print("yes")
                        
                        
                        image_1 = request.FILES.get('heading_image_1',None)
                        
                        if image_1:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_1.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_1.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.heading_image_1 = image_1
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass 
                    
                    
                    if 'section_2_image_field' in request.FILES:
                        
                        
                        image_2 = request.FILES.get('section_2_image_field',None)
                        
                        if image_2:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_2.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_2.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_2_images = image_2
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass
                    
                    if 'partnership_banner_1_field' in request.FILES:
                        
                        
                        image_3 = request.FILES.get('partnership_banner_1_field',None)
                        
                        if image_3:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_3.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_3.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_3_image = image_3
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass 
                    
                    if 'ads_image_1' in request.FILES:
                        
                        
                        image_4 = request.FILES.get('ads_image_1',None)
                        
                        if image_4:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_4.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_4.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_4_image = image_4
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass   
                    
                    if 'premium_banner_1_field' in request.FILES:
                        
                        
                        image_5 = request.FILES.get('premium_banner_1_field',None)
                        
                        if image_5:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_5.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_5.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_5_image = image_5
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass   
                    
                    
                    if 'social-media-section-image-field' in request.FILES:
                        
                        
                        image_6 = request.FILES.get('social-media-section-image-field',None)
                        
                        if image_6:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_6.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_6.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_6_logo = image_6
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass  
                    
                    if 'social-media-section-back-image-field' in request.FILES:
                        
                        
                        image_7 = request.FILES.get('social-media-section-back-image-field',None)
                        
                        if image_7:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_7.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_7.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_6_image = image_7
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass  
                    
                    if 'competition-section-section-image-field' in request.FILES:
                        
                        
                        image_8 = request.FILES.get('competition-section-section-image-field',None)
                        
                        if image_8:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_8.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_8.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        saveadvertiseetail.section_9_image = image_8
                                        print("image_saved")

                            except Exception as e:
                                    messages.error(request,str(e))    

                    else:
                        pass   
                    
                     
                    
                    saveadvertiseetail.save()
                    
                    if "dyanmic_deleted_section_field" in request.POST:
                            
                            try:
                                dynamic_section_data = request.POST.get('dyanmic_deleted_section_field')
                                dynamic_deleted_section_list = dynamic_section_data.split(',')
                                print(dynamic_deleted_section_list)
                                
                                for i in range(len(dynamic_deleted_section_list)):
                                    
                                    
                                    deletingviewfrom_data = cms_advertise_section_2_dynamic_field.objects.filter(field_id = dynamic_deleted_section_list[i]).delete()

                                
                            except Exception as e:
                                print("error: "+e)    

                                messages.error(request, str(e))  
                    
                    if "dynamic_deleted_partner_field" in request.POST:
                            
                            try:
                                dynamic_partner_data = request.POST.get('dynamic_deleted_partner_field')
                                dynamic_deleted_partner_list = dynamic_partner_data.split(',')
                                print(dynamic_deleted_partner_list)
                                
                                for i in range(len(dynamic_deleted_partner_list)):
                                    
                                    
                                    deletingviewfrom_data = cms_advertise_Partnership_dynamic_field.objects.filter(field_id = dynamic_deleted_partner_list[i]).delete()

                                
                            except Exception as e:
                                print("error: "+e)    

                                messages.error(request, str(e))       
                    
                    if "dyanmic_deleted_ads_field" in request.POST:
                            
                            try:
                                dynamic_ads_data = request.POST.get('dyanmic_deleted_ads_field')
                                dynamic_deleted_ads_list = dynamic_ads_data.split(',')
                                print(dynamic_deleted_ads_list)
                                
                                for i in range(len(dynamic_deleted_ads_list)):
                                    
                                    
                                    deletingviewfrom_data = cms_advertise_ads_dynamic_field.objects.filter(field_id = dynamic_deleted_ads_list[i]).delete()

                                
                            except Exception as e:
                                print("error: "+e)    

                                messages.error(request, str(e))  
                    
                    if "dynamic_deleted_premium_field" in request.POST:
                            
                            try:
                                dynamic_premium_data = request.POST.get('dynamic_deleted_premium_field')
                                dynamic_deleted_premium_list = dynamic_premium_data.split(',')
                                print(dynamic_deleted_premium_list)
                                
                                for i in range(len(dynamic_deleted_premium_list)):
                                    
                                    
                                    deletingviewfrom_data = cms_advertise_premium_dynamic_field.objects.filter(field_id = dynamic_deleted_premium_list[i]).delete()

                                
                            except Exception as e:
                                print("error: "+e)    

                                messages.error(request, str(e))                                  

                   
                    #dom = "True"
                    messages.success(request, "Advertise Page Updated Successfully")
                               
                except Exception as e:
                    print(str(e))
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': "hell"
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
            
        except Exception as e:
            messages.error(request, str(e))

            
               
#home page
@method_decorator(user_role_check, name='dispatch')
class cms_homepage(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/home.html"

    def get(self, request):
        features = cms_home_dynamic_field.objects.all()
        features_data = cms_pages.objects.get(id="1")
        
        achivements = cms_home_dynamic_achivements_field.objects.all()
        
        
        return render(
            request,
            self.template_name,
            {'features': features,'data':features_data,'achivements':achivements}        
    )  

#cms home
@user_role_check
@csrf_exempt
def savehomedetail(request):
        try:
            if request.method == "POST":
                #text
                
                heading_title_en = request.POST.get('home_heading_title_en')
                heading_title_ar = request.POST.get('home_heading_title_ar')
                heading_content_en = request.POST.get('home_heading_content_en')
                heading_content_ar = request.POST.get('home_heading_content_ar')
                sub_heading_1_name_en = request.POST.get('home_sub_heading_1_name_en')
                sub_heading_1_name_ar = request.POST.get('home_sub_heading_1_name_ar')
                sub_heading_1_title_en = request.POST.get('home_sub_heading_1_title_en')
                sub_heading_1_title_ar = request.POST.get('home_sub_heading_1_title_ar')
                sub_heading_section_2_title_en = request.POST.get('home_sub_heading_section_2_Title_en')
                sub_heading_section_2_title_ar = request.POST.get('home_sub_heading_section_2_Title_ar')
                sub_heading_section_2_content_en = request.POST.get('home_sub_heading_section_2_content_en')
                sub_heading_section_2_content_ar = request.POST.get('home_sub_heading_section_2_content_ar')
                sub_heading_section_2_title_1_en = request.POST.get('home_sub_heading_section_2_Title_1_en')
                sub_heading_section_2_title_1_ar = request.POST.get('home_sub_heading_section_2_Title_1_ar')
                sub_heading_section_2_content_1_en = request.POST.get('home_sub_heading_section_2_content_1_en')
                sub_heading_section_2_content_1_ar = request.POST.get('home_sub_heading_section_2_content_1_ar')
                empower_section_name_en = request.POST.get('empower_section_name_en')
                empower_section_name_ar = request.POST.get('empower_section_name_ar')
                empower_section_title_en = request.POST.get('empower_section_title_en')
                empower_section_title_ar = request.POST.get('empower_section_title_ar')
                empower_section_content_en = request.POST.get('empower_section_content_en')
                empower_section_content_ar = request.POST.get('empower_section_content_ar')
                features_section_name_en = request.POST.get('features_section_name_en')
                features_section_name_ar = request.POST.get('features_section_name_ar')
                features_section_title_en = request.POST.get('features_section_title_en')
                features_section_title_ar = request.POST.get('features_section_title_ar')
                features_section_content_en = request.POST.get('features_section_content_en')
                features_section_content_ar = request.POST.get('features_section_content_ar')
                features_section_form_title_en_1 = request.POST.get('features_section_form_title_en_1')
                features_section_form_title_ar_1 = request.POST.get('features_section_form_title_ar_1')
                features_section_form_content_en_1 = request.POST.get('features_section_form_content_en_1')
                features_section_form_content_ar_1 = request.POST.get('features_section_form_content_ar_1')
                spirit_section_title_en = request.POST.get('spirit_section_title_en')
                spirit_section_title_ar = request.POST.get('spirit_section_title_ar')
                spirit_section_content_en = request.POST.get('spirit_section_content_en')
                spirit_section_content_ar = request.POST.get('spirit_section_content_ar')
                team_name_en = request.POST.get('Team_name_en')
                team_name_ar = request.POST.get('Team_name_ar')
                team_title_en = request.POST.get('Team_title_en')
                team_title_ar = request.POST.get('Team_title_ar')
                achievements_heading_name_en = request.POST.get('achivements_heading_name_en')
                achivement_sec_1_heading_en = request.POST.get('achivement_heading_title_en')
                achivement_sec_1_heading_ar = request.POST.get('achivement_heading_title_ar')
                achivement_sec_1_title_en = request.POST.get('achivement_sec_title_en')
                achivement_sec_1_title_ar = request.POST.get('achivement_sec_title_ar')


                achievements_heading_name_ar = request.POST.get('achivements_heading_name_ar')
                achievements_heading_title_en = request.POST.get('achivements_heading_title_en')
                achievements_heading_title_ar = request.POST.get('achivements_heading_title_ar')
                explore_heading_name_en = request.POST.get('explore_heading_name_en')
                explore_heading_name_ar = request.POST.get('explore_heading_name_ar')
                explore_heading_title_en = request.POST.get('explore_heading_title_en')
                explore_heading_title_ar = request.POST.get('explore_heading_title_ar')
                blognews_heading_name_en = request.POST.get('blognews_heading_name_en')
                blognews_heading_name_ar = request.POST.get('blognews_heading_name_ar')
                blognews_heading_title_en = request.POST.get('blognews_sheading_title_en')
                blognews_heading_title_ar = request.POST.get('blognews_sheading_title_ar')
                partners_heading_name_en = request.POST.get('partners_heading_name_en')
                partners_heading_name_ar = request.POST.get('partners_heading_name_ar')
                partners_heading_title_en = request.POST.get('partners_heading_title_en')
                partners_heading_title_ar = request.POST.get('partners_heading_title_ar')
                seo_title_en = request.POST.get('seo_title_en')
                seo_title_ar = request.POST.get('seo_title_ar')
                seo_content_en = request.POST.get('seo_content_en')
                seo_content_ar = request.POST.get('seo_content_ar')
                
                features = []
                i = 1
                while True:
                    title_en = request.POST.get(f'features_section_form_title_en_{i}')
                    title_ar = request.POST.get(f'features_section_form_title_ar_{i}')
                    content_en = request.POST.get(f'features_section_form_content_en_{i}')
                    content_ar = request.POST.get(f'features_section_form_content_ar_{i}')

                    print(title_en)
                    if title_en or title_ar or content_en or content_ar:
                        features.append({
                            'title_en': title_en,
                            'title_ar': title_ar,
                            'content_en': content_en,
                            'content_ar': content_ar,
                        })
                        i += 1
                    else:
                        break
                #dom = "Done"
                #imageName = []
                
                try:
                    #savenewsdetail = cms_pages.objects.get(id = "5")
                    
                    savehomedetail = cms_pages.objects.get(id="1")

                    savehomedetail.heading_title_en = heading_title_en
                    savehomedetail.heading_title_ar = heading_title_ar
                    savehomedetail.heading_content_en = heading_content_en
                    savehomedetail.heading_content_ar = heading_content_ar
                    savehomedetail.sub_heading_name_en = sub_heading_1_name_en
                    savehomedetail.sub_heading_name_ar = sub_heading_1_name_ar
                    savehomedetail.sub_heading_title_en = sub_heading_1_title_en 
                    savehomedetail.sub_heading_title_ar = sub_heading_1_title_ar 
                    savehomedetail.sub_heading_logo_title_1_en = sub_heading_section_2_title_en  
                    savehomedetail.sub_heading_logo_title_1_ar = sub_heading_section_2_title_ar  
                    savehomedetail.sub_heading_logo_content_1_en = sub_heading_section_2_content_en 
                    savehomedetail.sub_heading_logo_content_1_ar = sub_heading_section_2_content_ar 
                    savehomedetail.sub_heading_logo_title_2_en  = sub_heading_section_2_title_1_en
                    savehomedetail.sub_heading_logo_title_2_ar  = sub_heading_section_2_title_1_ar
                    savehomedetail.sub_heading_logo_content_2_en  = sub_heading_section_2_content_1_en
                    savehomedetail.sub_heading_logo_content_2_ar  = sub_heading_section_2_content_1_ar
                    savehomedetail.section_2_heading_en   = empower_section_name_en
                    savehomedetail.section_2_heading_ar   = empower_section_name_ar
                    savehomedetail.section_2_title_en   = empower_section_title_en 
                    savehomedetail.section_2_title_ar   = empower_section_title_ar
                    savehomedetail.section_2_content_en   = empower_section_content_en
                    savehomedetail.section_2_content_ar   = empower_section_content_ar
                    savehomedetail.section_3_heading_en   = features_section_name_en
                    savehomedetail.section_3_heading_ar   = features_section_name_ar
                    savehomedetail.section_3_title_en   = features_section_title_en
                    savehomedetail.section_3_title_ar   = features_section_title_ar
                    savehomedetail.section_3_content_en   = features_section_content_en
                    savehomedetail.section_3_content_ar   = features_section_content_ar
                    savehomedetail.section_3_feature_title_en = features_section_form_title_en_1
                    savehomedetail.section_3_feature_title_ar = features_section_form_title_ar_1
                    savehomedetail.section_3_feature_short_content_en = features_section_form_content_en_1
                    savehomedetail.section_3_feature_short_content_ar = features_section_form_content_ar_1
                    savehomedetail.section_4_title_en = spirit_section_title_en
                    savehomedetail.section_4_title_ar = spirit_section_title_ar
                    savehomedetail.section_4_content_en = spirit_section_content_en 
                    savehomedetail.section_4_content_ar = spirit_section_content_ar 
                    savehomedetail.section_5_heading_en = team_name_en 
                    savehomedetail.section_5_heading_ar = team_name_ar 
                    savehomedetail.section_5_title_en = team_title_en 
                    savehomedetail.section_5_title_ar = team_title_ar 
                    savehomedetail.section_6_heading_en = achievements_heading_name_en
                    savehomedetail.section_6_heading_ar = achievements_heading_name_ar
                    savehomedetail.section_6_title_en  = achievements_heading_title_en
                    savehomedetail.section_6_title_ar  = achievements_heading_title_ar
                    savehomedetail.section_8_heading_en  = explore_heading_name_en
                    savehomedetail.section_8_heading_ar  = explore_heading_name_ar
                    savehomedetail.section_8_title_en  = explore_heading_title_en
                    savehomedetail.section_8_title_ar  = explore_heading_title_ar
                    savehomedetail.section_9_heading_en = blognews_heading_name_en
                    savehomedetail.section_9_heading_ar = blognews_heading_name_ar
                    savehomedetail.section_9_title_en = blognews_heading_title_en
                    savehomedetail.section_9_title_ar = blognews_heading_title_ar
                    savehomedetail.section_10_heading_en = partners_heading_name_en
                    savehomedetail.section_10_heading_ar = partners_heading_name_ar
                    savehomedetail.section_10_title_en  = partners_heading_title_en
                    savehomedetail.section_10_title_ar  = partners_heading_title_ar
                    
                    savehomedetail.achivement_heading_en = achivement_sec_1_heading_en
                    savehomedetail.achivement_heading_ar = achivement_sec_1_heading_ar
                    savehomedetail.achivement_title_en= achivement_sec_1_title_en 
                    savehomedetail.achivement_title_ar= achivement_sec_1_title_ar

                    savehomedetail.meta_title_en  = seo_title_en
                    savehomedetail.meta_title_ar  = seo_title_ar
                    savehomedetail.meta_content_en  = seo_content_en
                    savehomedetail.meta_content_ar   = seo_content_ar

                    '''if 'heading_banner' in request.FILES:
                        
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
                        pass'''
                    
                    '''savenewsdetail.section_2_title_en = heading_title_en
                    savenewsdetail.section_2_title_ar = heading_title_ar
                    savenewsdetail.section_2_content_en = heading_content_en
                    savenewsdetail.section_2_content_ar = heading_content_ar
                    savenewsdetail.meta_title_en = seo_title_en
                    savenewsdetail.meta_title_ar = seo_title_ar
                    savenewsdetail.meta_content_en = seo_content_en
                    savenewsdetail.meta_content_ar = seo_content_ar

                    savenewsdetail.save()'''
                    
                    
                    feature_count = request.POST.get('features_passed')
                    
                    print("this is feature: "+str(feature_count))
                    if feature_count:
                        for i in range(int(feature_count)+1):
                            
                            dom = i+1
                            image = 0
                            print("loop: "+str(dom))
                            feature_title_en = request.POST.get('features_section_form_title_en_{}'.format(str(dom)))
                            feature_title_ar = request.POST.get('features_section_form_title_ar_{}'.format(str(dom)))
                            feature_content_en = request.POST.get('features_section_form_content_en_{}'.format(str(dom)))
                            feature_content_ar = request.POST.get('features_section_form_content_ar_{}'.format(str(dom)))
                            feature_field = request.POST.get('id')
                            unique_id = request.POST.get('uid_{}'.format(dom))
                            print(unique_id)
                            print("title_ar {}: ".format(dom)+str(feature_title_ar))
                            
                            existing_record = cms_home_dynamic_field.objects.filter(field_id=unique_id).first()
                            print("exisiting: "+str(existing_record))
                            
                            if 'image_{}'.format(str(dom)) in request.FILES:
                                
                                image = request.FILES.get('image_{}'.format(str(dom)),None)
                                print("image: "+str(image))
                                
                                if image:
                                    try:
                                        save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                        # Save the file
                                        with open(save_path, 'wb+') as destination:
                                            for chunk in image.chunks():
                                                destination.write(chunk)
                                                #imageName.append(heading_banner.name)
                                                #savenewsdetail.heading_banner = heading_banner

                                    except Exception as e:
                                        dom = str(e)
                                
                            if existing_record:
                                    # Update the existing record
                                    existing_record.title_en = feature_title_en
                                    existing_record.title_ar = feature_title_ar
                                    existing_record.content_en = feature_content_en
                                    existing_record.content_ar = feature_content_ar
                                    
                                    if image:  # Update the image if a new one is uploaded
                                        existing_record.images = image

                                    existing_record.save()  # Save the updated record
                                    print("exsiting_title: "+str(existing_record.title_en))
                            else:        
                                savehomedynamcidetail = cms_home_dynamic_field(
                                            field_id=unique_id,
                                            title_en=feature_title_en,
                                            title_ar=feature_title_ar,
                                            content_en=feature_content_en,
                                            content_ar=feature_content_ar,
                                            images=image
                                )
                                savehomedynamcidetail.save()        
                                
                                print("last unique id: "+str(unique_id))
                            delete_record = cms_home_dynamic_field.objects.filter(field_id = None)
                            delete_record.delete()
                            
                             #achivement section
                    achive_count = request.POST.get('achive_passed')
                    
                    print("this is achive: "+str(achive_count))
                    if achive_count:
                        for i in range(int(achive_count)+1):
                            
                            dom = i+1
                            image = 0
                            print("loop: "+str(dom))
                            achive_title_en = request.POST.get('achive_section_form_htitle_en_{}'.format(str(dom)))
                            achive_title_ar = request.POST.get('achive_section_form_htitle_ar_{}'.format(str(dom)))
                            achive_content_en = request.POST.get('achive_section_form_title_en_{}'.format(str(dom)))
                            achive_content_ar = request.POST.get('achive_section_form_title_ar_{}'.format(str(dom)))
                            achive_field = request.POST.get('aid')
                            achive_unique_id = request.POST.get('uaid_{}'.format(dom))
                            print(achive_unique_id)
                            print("title_ar {}: ".format(dom)+str(achive_title_ar))
                            
                            existing_achive_record = cms_home_dynamic_achivements_field.objects.filter(field_id=achive_unique_id).first()
                            print("exisiting: "+str(existing_achive_record))

                            if existing_achive_record:
                                    # Update the existing record
                                    existing_achive_record.heading_en = achive_title_en
                                    existing_achive_record.heading_ar = achive_title_ar
                                    existing_achive_record.title_en = achive_content_en
                                    existing_achive_record.title_ar = achive_content_ar
                                    
                                

                                    existing_achive_record.save()  # Save the updated record
                                    print("exsiting_title: "+str(existing_achive_record.title_en))
                            else:        
                                savehomeachivedynamic = cms_home_dynamic_achivements_field(
                                            field_id=achive_unique_id,
                                            heading_en=achive_title_en,
                                            heading_ar=achive_title_ar,
                                            title_en=achive_content_en,
                                            title_ar=achive_content_ar,
                                )
                                savehomeachivedynamic.save()        
                                
                                print("last unique id: "+str(unique_id))
                            delete_record = cms_home_dynamic_achivements_field.objects.filter(field_id = None)
                            delete_record.delete()        

                        
                            #savehomedynamcidetail.save() 
                            '''print(feature_title_en)
                            print("this is id: "+feature_field)
                            if 'image_{}'.format(str(dom)) in request.FILES:
                                
                                image = request.FILES.get('image_{}'.format(str(dom)),None)
                                print("image: "+str(image))
                                
                                if image:
                                    try:
                                        save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image.name)
                                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                        # Save the file
                                        with open(save_path, 'wb+') as destination:
                                            for chunk in image.chunks():
                                                destination.write(chunk)
                                                #imageName.append(heading_banner.name)
                                                #savenewsdetail.heading_banner = heading_banner

                                    except Exception as e:
                                        dom = str(e)
                                
                                #savehomedynamcidetail = cms_home_dynamic_field(field_id = feature_field,title_en =feature_title_en,title_ar = feature_title_ar,content_en=feature_content_en,content_ar = feature_content_ar,images = image)
                            existing_record = cms_home_dynamic_field.objects.filter(field_id=feature_field).first()
                            print("exisiting: "+str(existing_record))
                            if existing_record:
                                    # Update the existing record
                                    existing_record.title_en = feature_title_en
                                    existing_record.title_ar = feature_title_ar
                                    existing_record.content_en = feature_content_en
                                    existing_record.content_ar = feature_content_ar
                                    
                                    if image:  # Update the image if a new one is uploaded
                                        existing_record.images = image

                                    existing_record.save()  # Save the updated record
                                    print(existing_record.title_en)
                            else:
                                    # Create a new record if one doesn't exist
                                    savehomedynamcidetail = cms_home_dynamic_field(
                                        field_id=feature_field,
                                        title_en=feature_title_en,
                                        title_ar=feature_title_ar,
                                        content_en=feature_content_en,
                                        content_ar=feature_content_ar,
                                        images=image
                                    )
                                    savehomedynamcidetail.save() 
                                #savehomedynamcidetail.save()     '''    
                        else:
                                pass 
                    savehomedetail.save()        
                    
                    deletedField = request.POST.get('deletedField')
                    print(deletedField)
                    
                    if deletedField !=0:
                        for i in range(int(deletedField)):
                            
                            deleted_id = request.POST.get('deleted_field_{}'.format(i))
                            print(deleted_id)
                            delete_the_record  = cms_home_dynamic_field.objects.filter(field_id = deleted_id ).delete()
                    else:
                        print("value is 0")    

                    achivedeletedField = request.POST.get('deletedachiveField')
                    print(achivedeletedField)
                    
                    if achivedeletedField !=0:
                        for i in range(int(achivedeletedField)):
                            
                            achivedeleted_id = request.POST.get('deleted_achivefield_{}'.format(i))
                            print(achivedeleted_id)
                            achviedelete_the_record  = cms_home_dynamic_achivements_field.objects.filter(field_id = achivedeleted_id ).delete()
                    else:
                        print("value is 0")    
                   
                    
                    if 'home_heading_section_image_1' in request.FILES:
                        
                        image_1 = request.FILES.get('home_heading_section_image_1',None)
                        
                        if image_1:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_1.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_1.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        savehomedetail.heading_image_1 = image_1

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    
                    if 'home_heading_section_image_2' in request.FILES:
                        
                        image_2 = request.FILES.get('home_heading_section_image_2',None)
                        print("image: "+str(image_2))
                        if image_2:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_2.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_2.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.heading_image_2 = image_2

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'home_heading_section_image_3' in request.FILES:
                        
                        image_3 = request.FILES.get('home_heading_section_image_3',None)
                        print("image: "+str(image_3))
                        if image_3:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_3.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_3.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.heading_image_3 = image_3

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'home_heading_section_icon' in request.FILES:
                        
                        image_4 = request.FILES.get('home_heading_section_icon',None)
                        print("image: "+str(image_4))
                        if image_4:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_4.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_4.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.sub_heading_logo = image_4

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                      
                    if 'home_heading_section_2_icon_1' in request.FILES:
                        
                        image_5 = request.FILES.get('home_heading_section_2_icon_1',None)
                        print("image: "+str(image_5))
                        if image_5:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_5.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_5.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.sub_heading_icon_1 = image_5

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'home_heading_section_2_icon_2' in request.FILES:
                        
                        image_6 = request.FILES.get('home_heading_section_2_icon_2',None)
                        print("image: "+str(image_6))
                        if image_6:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_6.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_6.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.sub_heading_icon_2 = image_6

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'empower_section_icon' in request.FILES:
                        
                        image_7 = request.FILES.get('empower_section_icon',None)
                        print("image: "+str(image_7))
                        if image_7:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_7.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_7.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_2_logo = image_7

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'empower_section_background_image' in request.FILES:
                        
                        image_8 = request.FILES.get('empower_section_background_image',None)
                        print("image: "+str(image_8))
                        if image_8:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_8.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_8.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_2_background = image_8

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'feature_image_1' in request.FILES:
                        
                        image_9 = request.FILES.get('feature_image_1',None)
                        print("image: "+str(image_9))
                        if image_9:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_9.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_9.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_3_feature_icons = image_9

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'spirit_icon_e' in request.FILES:
                        
                        image_10 = request.FILES.get('spirit_icon_e',None)
                        print("image: "+str(image_10))
                        if image_10:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_10.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_10.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_4_image = image_10

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass 
                    
                    if 'spirit_background_image' in request.FILES:
                        
                        image_11 = request.FILES.get('spirit_background_image',None)
                        print("image: "+str(image_11))
                        if image_11:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_11.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_11.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_4_background = image_11

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass
                    
                    if 'achivements_image_e' in request.FILES:
                        
                        image_12 = request.FILES.get('achivements_image_e',None)
                        print("image: "+str(image_12))
                        if image_12:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_12.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_12.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_5_image = image_12

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass  
                    
                    if 'testomonial_icon' in request.FILES:
                        
                        image_13 = request.FILES.get('testomonial_icon',None)
                        print("image: "+str(image_13))
                        if image_13:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_13.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_13.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_7_logo = image_13

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass  
                    
                    if 'testomonial_image_1' in request.FILES:
                        
                        image_14 = request.FILES.get('testomonial_image_1',None)
                        print("image 14: "+str(image_14))
                        if image_14:
                            try:
                                save_path = os.path.join(settings.MEDIA_ROOT, 'cmspages', image_14.name)
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                                # Save the file
                                with open(save_path, 'wb+') as destination:
                                    for chunk in image_14.chunks():
                                        destination.write(chunk)
                                        #imageName.append(heading_banner.name)
                                        #savenewsdetail.heading_banner = heading_banner
                                        savehomedetail.section_7_image = image_14

                            except Exception as e:
                                dom = str(e)
                    else:
                        pass  
                    #dom = "True"
                    savehomedetail.save()
                    messages.success(request, "Home Page Updated Successfully")
                               
                except Exception as e:
                    print(str(e))
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                        'heading_title_en': "hell"
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
            
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 

@method_decorator(user_role_check, name='dispatch')
class cms_Login(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/login.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(id='12')
        
        context = {
            'data':dataFilter,
        }
        dataFilter.meta_title_en
        return render(
            request,
            self.template_name,
            context
            
    ) 
        
#cms Login 
@csrf_exempt
@user_role_check
def savelogindetail(request):
        try:
            if request.method == "POST":
                print("hello")
                #text
                heading_title_en  = request.POST.get('login-title-en')
                heading_title_ar  = request.POST.get('login-title-ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                dom = "Done"
                
                try:
                    savelogindetail = cms_pages.objects.get(id = "12")

                    savelogindetail.heading_title_en = heading_title_en
                    savelogindetail.heading_title_ar = heading_title_ar
                    savelogindetail.meta_title_en = seo_title_en
                    savelogindetail.meta_title_ar = seo_title_ar
                    savelogindetail.meta_content_en = seo_content_en
                    savelogindetail.meta_content_ar = seo_content_ar

                    savelogindetail.save()
                    
                    dom = "True"
                    
                    messages.success(request, "Login Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 

@method_decorator(user_role_check, name='dispatch')           
class cms_registration(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/registration.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(id='13')
        
        context = {
            'data':dataFilter,
        }
        return render(
            request,
            self.template_name,
            context
            
    ) 
        
#cms Login
@user_role_check
@csrf_exempt
def saveregdetail(request):
        try:
            if request.method == "POST":
                print("hello")
                #text
                heading_title_en  = request.POST.get('reg-title-en')
                heading_title_ar  = request.POST.get('reg-title-ar')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                dom = "Done"
                
                try:
                    saveregdetail = cms_pages.objects.get(id = "13")

                    saveregdetail.heading_title_en = heading_title_en
                    saveregdetail.heading_title_ar = heading_title_ar
                    saveregdetail.meta_title_en = seo_title_en
                    saveregdetail.meta_title_ar = seo_title_ar
                    saveregdetail.meta_content_en = seo_content_en
                    saveregdetail.meta_content_ar = seo_content_ar

                    saveregdetail.save()
                    
                    dom = "True"
                    
                    messages.success(request, "Registration Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data)

@method_decorator(user_role_check, name='dispatch')         
class cms_dashboard(LoginRequiredMixin, View):
    template_name = "Admin/cmspages/dashboard.html"

    def get(self, request):
        
        dataFilter = cms_pages.objects.get(id='14')
        
        context = {
            'data':dataFilter,
        }
        return render(
            request,
            self.template_name,
            context
            
    ) 
        
#cms Login
@user_role_check
@csrf_exempt
def savedashdetail(request):
        try:
            if request.method == "POST":
                print("hello")
                #text
                heading_en  = request.POST.get('dash-title-en')
                heading_ar  = request.POST.get('dash-title-ar')
                heading_title_en  = request.POST.get('dash-title-en-1')
                heading_title_ar  = request.POST.get('dash-title-ar-1')
                seo_title_en  = request.POST.get('meta-title-en')
                seo_title_ar  = request.POST.get('meta-title-ar')
                seo_content_en  = request.POST.get('meta-content-en')
                seo_content_ar  = request.POST.get('meta-content-ar')
                
                dom = "Done"
                
                try:
                    savedashdetail = cms_pages.objects.get(id = "14")
                    
                    savedashdetail.heading_en = heading_en
                    savedashdetail.heading_ar = heading_ar
                    savedashdetail.heading_title_en = heading_title_en
                    savedashdetail.heading_title_ar = heading_title_ar
                    savedashdetail.meta_title_en = seo_title_en
                    savedashdetail.meta_title_ar = seo_title_ar
                    savedashdetail.meta_content_en = seo_content_en
                    savedashdetail.meta_content_ar = seo_content_ar

                    savedashdetail.save()
                    
                    dom = "True"
                    
                    messages.success(request, "Dashboard Page Updated Successfully")
                               
                except Exception as e:
                    messages.error(request,str(e))    
                      
                response_data = {
                        'status': 'success',
                        'message': 'Data uploaded successfully',
                }
                
                return JsonResponse(response_data)

            else:
                response_data = {'status': 'error', 'message': 'Missing data or image file'}

                return JsonResponse(response_data)
        except Exception as e:
               response_data = {'status': 'error', 'message': str(e)}

               return JsonResponse(response_data) 
        

# @method_decorator(user_role_check, name='dispatch')
class MobileDashboardBannerListView(View):
    template_name = "Admin/MobileApp/DasboardBanner/dashboard_banner_list.html"

    def get(self, request):
        banners = MobileDashboardBanner.objects.all()
        return render(
            request,
            self.template_name,
            {
                "banners": banners,
                "breadcrumb": {"child": "Mobile Dashboard Banners"},
            },
        )




# @method_decorator(user_role_check, name='dispatch')
class MobileDashboardBannerCreateView(View):
    # template_name = "Admin/General_Settings/MobileDashboardBanner_Create.html"

    def post(self, request):
        image_file = request.FILES.get("image")

        # Handling image upload
        image_file = request.FILES.get("image")
        image_name = None
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "dashboardbanner_images")
            )
            image_name = fs.save(image_file.name, image_file)
            image_name = "dashboardbanner_images/" + image_name

        MobileDashboardBanner.objects.create(
            image=image_name,  # Save the relative image path in the database
        )

        messages.success(request, "Banner created successfully.")
        return redirect("dashboard_banner_list")

# @method_decorator(user_role_check, name='dispatch')
class MobileDashboardBannerEditView(View):
    # template_name = "Admin/General_Settings/MobileDashboardBanner_Edit.html"

    def post(self, request, pk):
        banner_item = get_object_or_404(MobileDashboardBanner, pk=pk)

        image_file = request.FILES.get("image")
        if image_file:
            fs = FileSystemStorage(
                location=os.path.join(settings.MEDIA_ROOT, "dashboardbanner_images")
            )
            if banner_item.image and banner_item.image.path:
                old_image_path = banner_item.image.path
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            image_name = fs.save(image_file.name, image_file)
            banner_item.image = "dashboardbanner_images/" + image_name

        banner_item.save()
        messages.success(request, "Banner updated successfully.")
        return redirect("dashboard_banner_list")

# @method_decorator(user_role_check, name='dispatch')
class MobileDashboardBannerDeleteView(View):
    def post(self, request, pk):
        banner = get_object_or_404(MobileDashboardBanner, pk=pk)
        if banner.image and banner.image.path:
            old_image_path = banner.image.path
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        banner.delete()
        messages.success(request, "Banner deleted successfully.")
        return redirect("dashboard_banner_list")
    
    
    
######################################################### Report Module ###############################################
@method_decorator(user_role_check, name='dispatch')
class ReportListView(LoginRequiredMixin, View):
    template_name = "Admin/MobileApp/Report/report.html"

    def get(self, request):
        reports = Report.objects.all()
        return render(
            request,
            self.template_name,
            {
                "reports": reports,
                "breadcrumb": {"child": "Report List"},
            },
        )

@method_decorator(user_role_check, name='dispatch')
class ReportCreateView(View):
    def post(self, request):
        title_en = request.POST.get("title_en")
        content_en = request.POST.get("content_en")
        title_ar = request.POST.get("title_ar")
        content_ar = request.POST.get("content_ar")
        
        if not title_en or not content_en or not title_ar or not content_ar:
            messages.error(request, "Title and Description are required.")
            return redirect("report_list")

        # if not title_en or  content_en or  title_ar or  content_ar:
        #     messages.error(request, "Title and Content are required.")
        #     return redirect("report_list")

        report = Report.objects.create(
            title_en=title_en,
            title_ar=title_ar,
            content_en=content_en,
            content_ar=content_ar,
        )
            
        messages.success(request, "Report created successfully.")
        return redirect("report_list")

@method_decorator(user_role_check, name='dispatch')
class ReportEditView(View):
    template_name = "Admin/MobileApp/Report/report.html"

    def get(self, request, report_id):
        # Get the report object based on the ID
        report_item = get_object_or_404(Report, id=report_id)

        # Prepare context with existing report data
        context = {
            'report': report_item,  # Send the old data to the template
        }

        # Render the template with old report data
        return render(request, self.template_name, context)

    def post(self, request, report_id):
        # Get the report object to be updated
        report_item = get_object_or_404(Report, id=report_id)

        # Fetch new data from the form submission
        title_en = request.POST.get("title_en")
        content_en = request.POST.get("content_en")
        title_ar = request.POST.get("title_ar")
        content_ar = request.POST.get("content_ar")

        

        # Update the report with new data
        report_item.title_en = title_en
        report_item.title_ar = title_ar
        report_item.content_en = content_en
        report_item.content_ar = content_ar
        report_item.save()

        messages.success(request, "Report updated successfully.")
        return redirect("report_list")

@method_decorator(user_role_check, name='dispatch')
class ReportDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.delete()
        messages.success(request, "Report deleted successfully.")
        return redirect("report_list")
    
    
######################################################### Post  Report's List Module ###############################################

@method_decorator(user_role_check, name='dispatch')
class PostReportListView(LoginRequiredMixin, View):
    template_name = "Admin/MobileApp/Post_Report.html"

    def get(self, request):
        reports = PostReport.objects.select_related('post_id', 'report_id').order_by('-created_at').all()


        for report in reports:
            if report.creator_type == PostReport.USER_TYPE:

                report.user_info = User.objects.filter(id=report.created_by_id).first()
            elif report.creator_type == PostReport.TEAM_TYPE:

                report.user_info = Team.objects.filter(id=report.created_by_id).first()
            elif report.creator_type == PostReport.GROUP_TYPE:

                report.user_info = TrainingGroups.objects.filter(id=report.created_by_id).first()
            else:
                report.user_info = None  

        return render(
            request,
            self.template_name,
            {
                "reports": reports,
                "breadcrumb": {"child": "Reported Post's"},
            },
        )
        
@method_decorator(user_role_check, name='dispatch')
class PostReportDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(PostReport, pk=pk)
        print(pk)
        post = report.post_id
        
        post.delete()
        
        messages.success(request, "Post deleted successfully.")
        return redirect('post_report_list')
    
    
######################################################### Team List Module ###############################################
    
    
@method_decorator(user_role_check, name='dispatch')
class TeamListView(LoginRequiredMixin, View):
    template_name = "Admin/MobileApp/List_Of_Teams/Team_List.html"
    
    def get(self, request):
        teams = Team.objects.all()
        return render(
            request,
            self.template_name,
            {
                "teams": teams,
                "breadcrumb": {"child": "Team Lists"},
            },
        )

@method_decorator(user_role_check, name='dispatch')
class TeamDetailView(LoginRequiredMixin, View):
    template_name = "Admin/MobileApp/List_Of_Teams/Team_Details.html"  

    def get_team_related_data(self, team):
        branches = TeamBranch.objects.filter(team_id=team)
        sponsors = Sponsor.objects.filter(created_by_id=team.id , creator_type = 2)
        posts = Post.objects.filter(created_by_id=team.id, creator_type = 2)
        events = Event.objects.filter(created_by_id=team.id, creator_type = 2)
        return branches, sponsors, posts, events

    def get(self, request):
        team = request.GET.get('team_id') 
        
        try:
            branches, sponsors, posts, events = self.get_team_related_data(team)

            return render(
                request,
                self.template_name,
                {
                    "team": team,
                    "branches": branches,
                    "sponsors": sponsors,
                    "posts": posts,
                    "events": events,
                    "breadcrumb": {"child": "Team Detail"},
                },
            )
        except Team.DoesNotExist:
            return redirect('Dashboard')  

    def post(self, request):
        team_id = request.POST.get('team_id')  
        if not team_id:
            return redirect('Dashboard')  

        try:
            team = Team.objects.get(id=team_id)
            branches, sponsors, posts, events = self.get_team_related_data(team)

            return render(
                request,
                self.template_name,
                {
                    "team": team,
                    "branches": branches,
                    "sponsors": sponsors,
                    "posts": posts,
                    "events": events,
                    "breadcrumb": {"child": "Team Detail"},
                },
            )
        except Team.DoesNotExist:
            return redirect('Dashboard')
        
        
        
@method_decorator(user_role_check, name='dispatch')
class BranchDetailView(LoginRequiredMixin, View):
    template_name = "Admin/MobileApp/List_Of_Teams/Branch_Details.html" 

    def get_branch_related_data(self, branch):
        branches = TeamBranch.objects.filter(team_id=branch.id)
        members = JoinBranch.objects.filter(id=branch.id)
        tournaments = Tournament.objects.filter(team_id=branch.id)
        games = TournamentGames.objects.filter()
        return branches,members,tournaments,games

    def get(self, request):
        branch = request.GET.get('team_id')
     
        try:
            branches, members, tournaments, games = self.get_branch_related_data(branch)

            return render(
                request,
                self.template_name,
                {
                    "branch": branch,
                    "branches": branches,
                    "members": members,
                    "tournaments": tournaments,
                    "games": games,
                    "breadcrumb": {"child": "Branch Detail"},
                },
            )
        except TeamBranch.DoesNotExist:
            return redirect('Dashboard')
    
    def post(self, request):
        branch_id = request.POST.get('branch_id')  

        try:
            branch = TeamBranch.objects.get(id=branch_id)
            branches, members, tournaments, games = self.get_branch_related_data(branch)
            return render(
                request,
                self.template_name,
                {
                    "branch": branch,
                    "branches": branches,
                    "members": members,
                    "tournaments": tournaments,
                    "games": games,
                    "breadcrumb": {"child": "Branch Detail"},
                },
            )
        except TeamBranch.DoesNotExist:
            return redirect('Dashboard')
        
        
######################### Playing Position #############################

@method_decorator(user_role_check, name='dispatch')
class PlayingPositionListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/playing_position.html"

    def get(self, request):
        playing_positions = PlayingPosition.objects.all()
        return render(
            request,
            self.template_name,
            {
                "playing_positions": playing_positions,
                "breadcrumb": {"child": "Playing Positions List"},
            },
        )

@method_decorator(user_role_check, name='dispatch')
class PlayingPositionCreateView(LoginRequiredMixin,View):
    def post(self, request):
        name_en=request.POST.get("name_en")
        name_ar=request.POST.get("name_ar")
        shortname=request.POST.get("shortname")

                
        if not name_en or not name_ar or not shortname :
            messages.error(request, "Title and Description are required.")
            return redirect("playing_position_list")

       
        playing_positions = PlayingPosition.objects.create(
            name_en=name_en,
            name_ar=name_ar,
            shortname=shortname,
        
        )
            
        messages.success(request, "Playing Position Added successfully.")
        return redirect("playing_position_list")

@method_decorator(user_role_check, name='dispatch')
class PlayingPositionEditView(LoginRequiredMixin,View):
    template_name = "Admin/General_Settings/playing_position.html"

    def get(self, request, playing_position_id):
        # Get the report object based on the ID
        playing_positions = get_object_or_404(PlayingPosition, id=playing_position_id)

        # Prepare context with existing report data
        context = {
            'playing_positions': playing_positions,  # Send the old data to the template
        }

        # Render the template with old report data
        return render(request, self.template_name, context)

    def post(self, request, playing_position_id):
        # Get the report object to be updated
        playing_positions = get_object_or_404(PlayingPosition, id=playing_position_id)

        # Fetch new data from the form submission
        name_en=request.POST.get("name_en")
        name_ar=request.POST.get("name_ar")
        shortname=request.POST.get("shortname")


        

        # Update the report with new data
        playing_positions.name_en = name_en
        playing_positions.name_ar = name_ar
        playing_positions.shortname = shortname
     
        playing_positions.save()

        messages.success(request, "Playing Positions updated successfully.")
        return redirect("playing_position_list")



################################################################# AgeGroup CRUD Views ###################################################
@method_decorator(user_role_check, name='dispatch')
class AgeGroupCreateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AgeGroup.html"

    def get(self, request):
        form = AgeGroupForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AgeGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Age Group Created successfully.")
            return redirect("agegroup_list")
        messages.error(
            request,
            "There was an error creating the age group. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class AgeGroupUpdateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AgeGroup.html"  # Fixed template name

    def get(self, request, pk):
        agegroup = get_object_or_404(AgeGroup, pk=pk)
        form = AgeGroupForm(instance=agegroup)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        agegroup = get_object_or_404(AgeGroup, pk=pk)
        form = AgeGroupForm(request.POST, instance=agegroup)
        if form.is_valid():
            form.save()
            messages.success(request, "AgeGroup Updated Successfully.")
            return redirect("agegroup_list")
        messages.error(
            request,
            "There was an error updating the agegroup. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class AgeGroupDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        agegroup = get_object_or_404(AgeGroup, pk=pk)
        agegroup.delete()
        messages.success(request, "AgeGroup Deleted Successfully.")
        return redirect("agegroup_list")

    def post(self, request, pk):
        agegroup = get_object_or_404(AgeGroup, pk=pk)
        agegroup.delete()
        messages.success(request, "AgeGroup Deleted Successfully.")
        return redirect("agegroup_list")

@method_decorator(user_role_check, name='dispatch')
class AgeGroupListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AgeGroup.html"

    def get(self, request):
        agegroup = AgeGroup.objects.all()
        return render(
            request,
            self.template_name,
            {"agegroup": agegroup, "breadcrumb": {"parent": "User", "child": "Age Group"}},
        )



################################################################# Injury Type CRUD Views ###################################################
@method_decorator(user_role_check, name='dispatch')
class InjuryTypeCreateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/InjuryType.html"

    def get(self, request):
        form = InjuryTypeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = InjuryTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Injury Type Created successfully.")
            return redirect("injurytype_list")
        messages.error(
            request,
            "There was an error creating the age group. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class InjuryTypeUpdateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/InjuryType.html"  # Fixed template name

    def get(self, request, pk):
        injurytype = get_object_or_404(InjuryType, pk=pk)
        form = InjuryTypeForm(instance=injurytype)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        injurytype = get_object_or_404(InjuryType, pk=pk)
        form = InjuryTypeForm(request.POST, instance=injurytype)
        if form.is_valid():
            form.save()
            messages.success(request, "Injury Type Updated Successfully.")
            return redirect("injurytype_list")
        messages.error(
            request,
            "There was an error updating the injury type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class InjuryTypeDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        injurytype = get_object_or_404(InjuryType, pk=pk)
        injurytype.delete()
        messages.success(request, "Injur Type Deleted Successfully.")
        return redirect("injurytype_list")

    def post(self, request, pk):
        injurytype = get_object_or_404(InjuryType, pk=pk)
        injurytype.delete()
        messages.success(request, "Injury Type Deleted Successfully.")
        return redirect("injurytype_list")

@method_decorator(user_role_check, name='dispatch')
class InjuryTypeListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/InjuryType.html"

    def get(self, request):
        injurytype = InjuryType.objects.all()
        return render(
            request,
            self.template_name,
            {"injurytype": injurytype, "breadcrumb": {"parent": "User", "child": "Injury Type"}},
        )


################################################################# Game Officials Type CRUD Views ###################################################
@method_decorator(user_role_check, name='dispatch')
class GameOfficialsTypeCreateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/GameOfficialsType.html"

    def get(self, request):
        form = GameOfficialsTypeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GameOfficialsTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Game Officials Type Created successfully.")
            return redirect("gameofficialstype_list")
        messages.error(
            request,
            "There was an error creating the age group. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class GameOfficialsTypeUpdateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/GameOfficialsType.html"  # Fixed template name

    def get(self, request, pk):
        gameofficialstype = get_object_or_404(OfficialsType, pk=pk)
        form = GameOfficialsTypeForm(instance=gameofficialstype)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        gameofficialstype = get_object_or_404(OfficialsType, pk=pk)
        form = GameOfficialsTypeForm(request.POST, instance=gameofficialstype)
        if form.is_valid():
            form.save()
            messages.success(request, "Game Officials Type Updated Successfully.")
            return redirect("gameofficialstype_list")
        messages.error(
            request,
            "There was an error updating the injury type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class GameOfficialsTypeDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        gameofficialstype = get_object_or_404(OfficialsType, pk=pk)
        gameofficialstype.delete()
        messages.success(request, "Injur Type Deleted Successfully.")
        return redirect("gameofficialstype_list")

    def post(self, request, pk):
        gameofficialstype = get_object_or_404(OfficialsType, pk=pk)
        gameofficialstype.delete()
        messages.success(request, "Game Officials Type Deleted Successfully.")
        return redirect("gameofficialstype_list")

@method_decorator(user_role_check, name='dispatch')
class GameOfficialsTypeListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/GameOfficialsType.html"

    def get(self, request):
        gameofficialstype = OfficialsType.objects.all()
        return render(
            request,
            self.template_name,
            {"gameofficialstype": gameofficialstype, "breadcrumb": {"parent": "User", "child": "Game Officials Type"}},
        )




################################################################# Account Delete Reason CRUD Views ###################################################
@method_decorator(user_role_check, name='dispatch')
class AccountDeleteReasonCreateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AccountDeleteReason.html"

    def get(self, request):
        form = AccountDeleteReasonForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AccountDeleteReasonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account Delete Reason Created successfully.")
            return redirect("accountdeletereason_list")
        messages.error(
            request,
            "There was an error creating the age group. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class AccountDeleteReasonUpdateView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AccountDeleteReason.html"  # Fixed template name

    def get(self, request, pk):
        accountdeletereason = get_object_or_404(UserDeleteReason, pk=pk)
        form = AccountDeleteReasonForm(instance=accountdeletereason)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        accountdeletereason = get_object_or_404(UserDeleteReason, pk=pk)
        form = AccountDeleteReasonForm(request.POST, instance=accountdeletereason)
        if form.is_valid():
            form.save()
            messages.success(request, "Account Delete Reason Updated Successfully.")
            return redirect("accountdeletereason_list")
        messages.error(
            request,
            "There was an error updating the injury type. Please ensure all fields are filled out correctly.",
        )
        return render(request, self.template_name, {"form": form})

@method_decorator(user_role_check, name='dispatch')
class AccountDeleteReasonDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        accountdeletereason = get_object_or_404(UserDeleteReason, pk=pk)
        accountdeletereason.delete()
        messages.success(request, "Injur Type Deleted Successfully.")
        return redirect("accountdeletereason_list")

    def post(self, request, pk):
        accountdeletereason = get_object_or_404(UserDeleteReason, pk=pk)
        accountdeletereason.delete()
        messages.success(request, "Account Delete Reason Deleted Successfully.")
        return redirect("accountdeletereason_list")

@method_decorator(user_role_check, name='dispatch')
class AccountDeleteReasonListView(LoginRequiredMixin, View):
    template_name = "Admin/General_Settings/AccountDeleteReason.html"

    def get(self, request):
        accountdeletereason = UserDeleteReason.objects.all()
        return render(
            request,
            self.template_name,
            {"accountdeletereason": accountdeletereason, "breadcrumb": {"parent": "User", "child": "Account Delete Reason"}},
        )


############################ User Assign ##########################
@method_decorator(user_role_check, name='dispatch')
class TournamentGamesListView(LoginRequiredMixin, View):
    template_name = "Admin/Assign_User_Game.html"

    def get(self, request):
        # Current time to compare game date and start time
        current_time = now()

        # Retrieve tournament games with annotated order for categorizing
        tournament_games = (
            TournamentGames.objects.annotate(
                assigned_user_name=F('game_statistics_handler__username'),  # Get the assigned user name
                is_unassigned=Case(
                    When(game_statistics_handler__isnull=True, then=1),
                    default=0,
                    output_field=IntegerField()
                ),
                is_upcoming=Case(
                    When(game_date__gt=current_time.date(), then=1),
                    When(game_date=current_time.date(), game_start_time__gt=current_time.time(), then=1),
                    default=0,
                    output_field=IntegerField()
                ),
                is_passed=Case(
                    When(game_date__lt=current_time.date(), then=1),
                    When(game_date=current_time.date(), game_start_time__lt=current_time.time(), then=1),
                    default=0,
                    output_field=IntegerField()
                ),
            )
            .order_by('-game_date', '-game_start_time', '-id')
        )

        return render(
            request,
            self.template_name,
            {
                "tournament_games": tournament_games,
                "breadcrumb": {"child": "Tournament Games List"},
            },
        )

@method_decorator(csrf_exempt, name='dispatch')
class AssignUserToGameView(LoginRequiredMixin, View):
    def post(self, request, game_id):
        try:
            # Parse JSON request body
            data = json.loads(request.body)
            user_id = data.get('user_id')

            # Validate and retrieve the game and user
            game = get_object_or_404(TournamentGames, id=game_id)
            user = get_object_or_404(User, id=user_id)

            current_time = now()

            # Check if the game date and time has passed
            if game.game_date < current_time.date() or (
                game.game_date == current_time.date() and game.game_start_time <= current_time.time()
            ):
                messages.success(
                request,
                f"Cannot assign user; game already started."
            )
                return JsonResponse(
                    {'error': 'Cannot assign user; game already started.'}, status=400
                )

            # Assign the user to the game
            game.game_statistics_handler = user
            game.save()

            messages.success(
                request,
                f"User assigned successfully!"
            )

            return JsonResponse({'message': 'User assigned successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'error': 'GET method not allowed'}, status=405)


def fetch_users(request):
    role_id = request.GET.get('role_id')
    phone = request.GET.get('phone', '')

    # Query users based on role ID and phone number filter
    users = User.objects.filter(
        role_id=role_id, phone__icontains=phone, is_deleted=False
    ).values('id', 'username', 'phone')
    return JsonResponse(list(users), safe=False)




################################# Finished Games ##################
# class TournamentGameListView(View):
#     template_name = "Admin/Games/ListOfGames.html"

#     def get(self, request):
#         games = TournamentGames.objects.filter(finish=True).select_related('tournament_id')
#         return render(
#             request,
#             self.template_name,
#             {
#                 "games": games,
#                 "breadcrumb": {"parent": "Tournaments", "child": "Games"},
#             },
#         )

#     def post(self, request):
#         """
#         Handles the form submission for editing games.
#         """
#         game_id = request.POST.get('game_id')
#         game = get_object_or_404(TournamentGames, pk=game_id)
#         form = TournamentGameForm(request.POST, instance=game)

#         if form.is_valid():
#             form.save()
#             return JsonResponse({"success": True, "message": "Game updated successfully."})
#         else:
#             return JsonResponse({"success": False, "errors": form.errors}, status=400)

#     def get_game_data(self, request, game_id):
#         """
#         Handles AJAX requests to get game details.
#         """
#         game = get_object_or_404(TournamentGames, pk=game_id)
#         form = TournamentGameForm(instance=game)
#         return render(request, "Admin/Games/ListOfGames.html", {"form": form, "game": game})
    

# class TournamentGameView(View):
#     template_name = "Admin/Games/ListOfGames.html"

#     def get(self, request, pk):
#         game = get_object_or_404(TournamentGames, pk=pk)
#         return render(request, self.template_name, {"game": game})

# class TournamentGameEditView(View):
#     template_name = "Admin/Games/edit_form.html"  # Separate template for the form

#     def get(self, request, pk):
#         game = get_object_or_404(TournamentGames, pk=pk)
#         form = TournamentGameForm(instance=game)
#         if request.is_ajax():
#             return render(request, self.template_name, {"form": form})
#         return JsonResponse({"error": "Invalid request"}, status=400)

#     def post(self, request, pk):
#         game = get_object_or_404(TournamentGames, pk=pk)
#         form = TournamentGameForm(request.POST, instance=game)
#         if form.is_valid():
#             form.save()
#             return JsonResponse({"success": True, "message": "Game updated successfully."})
#         return JsonResponse({"success": False, "errors": form.errors}, status=400)
@method_decorator(user_role_check, name='dispatch')
class TournamentGameStatsView(LoginRequiredMixin, View):
    template_name = "Admin/Games/ListOfGames.html"

    def get(self, request):
        games = TournamentGames.objects.all().select_related('tournament_id', 'team_a', 'team_b')
        return render(
            request,
            self.template_name,
            {"games": games, "breadcrumb": {"parent": "Tournament", "child": "Game Stats"}}
        )

@method_decorator(user_role_check, name='dispatch')
class TournamentGameEditStatsView(LoginRequiredMixin, View):
    template_name = "Admin/Games/EditGameStatsModal.html"

    def get(self, request, game_id):
        try:
            # Get the game object based on ID
            game = TournamentGames.objects.get(id=game_id)
            form = TournamentGameForm(instance=game)

            # Check if the request is AJAX (indicated by 'X-Requested-With' header)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Render the form as a string and return as JSON response
                html = render_to_string(self.template_name, {'form': form, 'game': game})
                return JsonResponse({'html': html})  # Return HTML as JSON object
            
            # Non-AJAX request, return regular response (optional, for regular page load)
            return render(request, 'Admin/Games/EditGameStatsModal.html', {'form': form, 'game': game})
        
        except ObjectDoesNotExist:
            # Return an error message as JSON if game is not found
            return JsonResponse({'error': 'Game not found'}, status=404)

        except Exception as e:
            # Handle other unexpected exceptions and return the error as JSON
            return JsonResponse({'error': str(e)}, status=500)
        
    def post(self, request, game_id):
        try:
            game = TournamentGames.objects.get(id=game_id)
        except TournamentGames.DoesNotExist:
            return redirect('games_list')  # Redirect if game does not exist

        form = TournamentGameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stats updated successfully!')
            return JsonResponse({'success': True})
        else:
            # Return the form with errors as HTML
            html = render_to_string(self.template_name, {'form': form, 'game': game})
            return JsonResponse({'success': False, 'html': html})