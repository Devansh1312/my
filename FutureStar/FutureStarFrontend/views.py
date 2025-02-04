# Standard Library Imports
import os
import time
import random
from datetime import datetime

# Third-party Imports
import jwt
import requests
from dotenv import load_dotenv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, When, Case, F
from django.utils import timezone
from django.utils.translation import activate
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from itertools import chain

# Application-Specific Imports
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarGameSystem.models import *
from FutureStarFriendlyGame.models import *
from FutureStarTrainingApp.models import *
from FutureStar import settings
from .forms import *
load_dotenv()  



def get_language(request):
    """
    Retrieves the language from the URL or session and updates the session values.
    Ensures the language is either 'en' or 'ar', defaulting to 'en'.
    """
    allowed_languages = {'en', 'ar'}
    language = request.GET.get('Language', '').lower()

    if language in allowed_languages:
        request.session['language'] = language
    else:
        language = request.session.get('language', 'en')
        if language not in allowed_languages:
            language = 'en'
        request.session['language'] = language

    request.session['current_language'] = language  # Keep 'current_language' consistent
    return language


##############################################   HomePage   ########################################################

class HomePage(View):
    def get(self, request, *args, **kwargs):
        # Use get_language to handle language logic
        language_from_url = get_language(request)

        # Retrieve other data as usual
        marquee = Slider_Content.objects.all().order_by('-id')
        app_features = App_Feature.objects.all().order_by('-id')
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all().order_by('-id')
        team_members = Team_Members.objects.all().order_by('id')
        cmsfeatures = cms_home_dynamic_field.objects.all() or None
        cms_home_dynamic_achivements = cms_home_dynamic_achivements_field.objects.all() or None
        number_of_users = User.objects.all().count()
        tournament_organized = Tournament.objects.all().count()
        team_created=Team.objects.all().count()
        games_played=TournamentGames.objects.all().count()

        try:
            cmsdata = cms_pages.objects.get(id=1)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        # Prepare context for rendering
        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
            "team_members": team_members,
            "cmsdata": cmsdata,
            "current_language": language_from_url,
            "cmsfeatures": cmsfeatures,
            "cms_home_dynamic_achivements": cms_home_dynamic_achivements,
            "number_of_users": number_of_users,
            "tournament_organized": tournament_organized,
            "team_created": team_created,
            "games_played": games_played,
        }
        
        # Render the home page with context
        return render(request, "home.html", context)
    
##############################################   DiscoverPage   ########################################################

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        dynamic = cms_dicovery_dynamic_image.objects.all()
        whyus = cms_dicovery_dynamic_view.objects.all()
        try:
            cmsdata = cms_pages.objects.get(id=2)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":language_from_url,
            "cmsdata" : cmsdata,
            "dynamic":dynamic,
            "whyus":whyus
        }
        return render(request, "discover.html",context)
    
##############################################   SuccessStoriesPage   ########################################################
class SuccessStoriesPage(View):
    def get(self, request, *args, **kwargs):
        # tryout_clubs = Tryout_Club.objects.all()
        language_from_url = get_language(request)
        try:
            cmsdata = cms_pages.objects.get(id=3)  # Use get() to fetch a single object
            latest_users = User.objects.all().order_by('-id')[:4]
            
            team_branches = TeamBranch.objects.all()
            
            
            team_wins = []

            for team_branch in team_branches:
                branches_win = TournamentGames.objects.filter(
                    winner_id=team_branch.id, finish=True
                )
                win_count = branches_win.count()
               
                team_wins.append({"team_branch": team_branch, "win_count": win_count})

            # Sort the team_wins list by win_count in descending order
            team_wins = sorted(team_wins, key=lambda x: x['win_count'], reverse=True)
           
            # Get the top 6 teams
            top_6_teams = team_wins[:6]
      
            
            user_data = []
            for user in latest_users:
                followers_count = FollowRequest.objects.filter(
                    target_id=user.id, target_type=FollowRequest.USER_TYPE
                ).count()
                following_count = FollowRequest.objects.filter(
                    created_by_id=user.id, creator_type=FollowRequest.USER_TYPE
                ).count()
                post_count = Post.objects.filter(
                    created_by_id=user.id, creator_type=FollowRequest.USER_TYPE
                ).count()
                
                user_data.append({
                    "user": user,
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "post_count": post_count,
                })
            
        except cms_pages.DoesNotExist:
            cmsdata = None
            user_data = []
            team_wins = []
            top_6_teams = []
        
        # Pass the data to the context
        context = {
            
            "cmsdata": cmsdata,
            "latest_users": latest_users,
            "user_data": user_data,
            "team_wins": team_wins,
            "top_6_teams": top_6_teams,  # Pass top 6 teams to context
            "current_language": language_from_url,
        }
        return render(request, "success-stories.html", context)

##############################################   NewsPage   ########################################################

class NewsPage(View):
    
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        try:
            cmsdata = cms_pages.objects.get(id=4)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        # Get the list of news
        news_list = News.objects.all().order_by('-id')

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(news_list, 6)  # Display 6 items per page
        
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)

        # Pass the current language and news to the template
        context = {
            "news": news,
            "current_language": language_from_url,
            "cmsdata" : cmsdata,
        }
        return render(request, "news.html", context)
    
    

##############################################   NewsDetailPage   ########################################################

class NewsDetailPage(View):
    def get(self, request, pk):
        language_from_url = get_language(request)
        # Get the news item based on the provided pk in the URL
        news = get_object_or_404(News, id=pk)

        # Fetch CMS data
        try:
            cmsdata = cms_pages.objects.get(id=5)
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        # Pass the current language and news to the template
        context = {
            "news": news,
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        }
        return render(request, "news-details.html", context)
    

##############################################   AdvertisePage   ########################################################

class AdvertisePage(View):
    
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        dynamic_field = cms_advertise_section_2_dynamic_field.objects.all()
        partnership_dynamic_field = cms_advertise_Partnership_dynamic_field.objects.all()
        ads_dynamic_field = cms_advertise_ads_dynamic_field.objects.all()
        premium_dynamic_field = cms_advertise_premium_dynamic_field.objects.all()

        try:
            cmsdata = cms_pages.objects.get(id=6)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":language_from_url,
            "cmsdata" : cmsdata,
            "dynamic_field":dynamic_field,
            "partnership_dynamic_field":partnership_dynamic_field,
            "ads_dynamic_field":ads_dynamic_field,
            "premium_dynamic_field":premium_dynamic_field,
        }
       
        return render(request, "advertise.html",context)


##############################################   AboutPage   ########################################################

class AboutPage(View):
    
    def get(self, request, *args, **kwargs):
        
        marquee = Slider_Content.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        global_clients = Global_Clients.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        number_of_users=User.objects.all().count()
        tournament_organized = Tournament.objects.all().count()
        team_created=Team.objects.all().count()
        games_played=TournamentGames.objects.all().count()
        language_from_url = request.GET.get('Language', None)
        
        language_from_url = get_language(request)
        try:
            cmsdata = cms_pages.objects.get(id=7)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "marquee": marquee,
            "testimonials": testimonials,
            "global_clients": global_clients,
            "current_language":language_from_url,
            "cmsdata" : cmsdata,
            "team_members" : team_members,
            "number_of_users": number_of_users,
            "tournament_organized": tournament_organized,
            "team_created": team_created,
            "games_played": games_played,

        }
        return render(request, "about.html",context)



##############################################   ContactPage   ########################################################

class ContactPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=8)  # Fetch the CMS data
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle case where the CMS data doesn't exist

        language_from_url = request.GET.get('Language', None)
        
        language_from_url = get_language(request)

        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        }
        return render(request, "contact.html", context)

    def post(self, request):
        # Fetch form data
        fullname = request.POST.get("fullname", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        language_from_url = request.GET.get('Language', None)
        
        language_from_url = get_language(request)
        try:
            cmsdata = cms_pages.objects.get(id=8)  # Fetch CMS data again for context
        except cms_pages.DoesNotExist:
            cmsdata = None

        # If no contact form fields are filled, assume the user is only changing the language
        if not fullname and not phone and not email and not message:
            messages.success(request, "Language changed successfully!")
            return redirect('contact')  # Redirect after language change

        # Validation: Ensure all fields are filled
        if not fullname or not phone or not email or not message:
            messages.error(request, "All fields are required for submitting an inquiry.")
            context = {
                "current_language": language_from_url,
                "cmsdata": cmsdata,
            }
            return render(request, "contact.html", context)

        # Save the inquiry
        Inquire.objects.create(
            fullname=fullname,
            phone=phone,
            email=email,
            message=message,
        )

        # Success message and redirect after submission
        messages.success(request, "Inquiry submitted successfully.")
        return redirect("contact")

##############################################   PrivacyPolicyPage   ########################################################

class PrivacyPolicyPage(View):
    
    def get(self, request, *args, **kwargs):

        language_from_url = get_language(request)
        try:
            cmsdata = cms_pages.objects.get(id=10)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist


        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        } 
        return render(request, "privacy-policy.html",context)

##############################################   TermsofServicesPage   ########################################################

class TermsofServicesPage(View):
    
    def get(self, request, *args, **kwargs):

        language_from_url = get_language(request)
        
        try:
            cmsdata = cms_pages.objects.get(id=9)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
            

        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        } 

        return render(request, "terms-of-services.html",context)
    
######################### terms-of-conditions #####################

class TermsAndConditionsPage(View):
    
    def get(self, request, *args, **kwargs):
        # Check if the 'Language' parameter is in the URL
        language_from_url = get_language(request)

        # Fetch the CMS data
        try:
            cmsdata = cms_pages.objects.get(id=11)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        
        context = {
            "current_language": language_from_url,  # Pass the language to the context
            "cmsdata": cmsdata,
        } 

        return render(request, "terms-and-conditions.html", context)
    
##############################################   PlayerDashboardPage   ########################################################

class PlayerDashboardPage(LoginRequiredMixin, View):
    
    def get_user_related_data(self, user, time_filter=None):
        """
        Fetch user-related data such as event bookings, teams, stats, and upcoming/latest games
        based on the user's role.
        """
        # Fetch event bookings
        # Fetch teams associated with the user
        teams = JoinBranch.objects.filter(user_id=user.id)

        # Initialize stats
        stats = {}

        # Fetch upcoming games based on the user's role
        if user.role.id == 2:  # Player role
            stats = self.get_player_stats(user, time_filter)
        elif user.role.id == 3:  # Coach role
            stats = self.get_coach_stats(user, time_filter)
        elif user.role.id == 4:  # Referee role
            stats = self.get_referee_stats(user, time_filter)
        elif user.role.id == 6:  # Manager role
            stats = self.get_manager_stats(user, time_filter)


        return teams, stats

    

    def get_player_stats(self, user, time_filter):
        """
        Fetch player-specific stats, including total wins, losses, draws, games played, goals, assists, and cards
        from both tournament and friendly games, and also return the upcoming games where the player is already in the lineup.
        """
        try:
            # Fetch the team the player is associated with
            team = JoinBranch.objects.filter(user_id=user.id).first()
            if not team:
                return {"status": 0, "message": "User is not associated with any team."}

            team_id = team.branch_id

            # Ensure time_filter is valid
            time_filter = time_filter or {}

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                (Q(team_a=team_id) | Q(team_b=team_id)),
                finish=True,
                **time_filter
            )
            tournament_total_games_played = tournament_games.count()

            tournament_goals = tournament_games.aggregate(
                total_goals_a=Sum('team_a_goal'),
                total_goals_b=Sum('team_b_goal')
            )
            tournament_total_goals_scored = tournament_goals['total_goals_a'] or 0
            tournament_total_goals_conceded = tournament_goals['total_goals_b'] or 0

            tournament_total_assists = PlayerGameStats.objects.filter(
                game_id__in=tournament_games.values_list('id', flat=True)
            ).aggregate(
                total_assists=Sum('assists')
            )['total_assists'] or 0

            tournament_total_wins = tournament_games.filter(winner_id=team_id).count()
            tournament_total_losses = tournament_games.filter(loser_id=team_id).count()
            tournament_total_draws = tournament_games.filter(is_draw=True).count()

            tournament_cards_stats = PlayerGameStats.objects.filter(
                game_id__in=tournament_games.values_list('id', flat=True)
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )
            tournament_total_yellow_cards = tournament_cards_stats['total_yellow_cards'] or 0
            tournament_total_red_cards = tournament_cards_stats['total_red_cards'] or 0

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                (Q(team_a=team_id) | Q(team_b=team_id)),
                finish=True,
                **time_filter
            )
            friendly_total_games_played = friendly_games.count()

            friendly_goals = friendly_games.aggregate(
                total_goals_a=Sum('team_a_goal'),
                total_goals_b=Sum('team_b_goal')
            )
            friendly_total_goals_scored = friendly_goals['total_goals_a'] or 0
            friendly_total_goals_conceded = friendly_goals['total_goals_b'] or 0

            friendly_total_assists = FriendlyGamesPlayerGameStats.objects.filter(
                game_id__in=friendly_games.values_list('id', flat=True)
            ).aggregate(
                total_assists=Sum('assists')
            )['total_assists'] or 0

            friendly_total_wins = friendly_games.filter(winner_id=team_id).count()
            friendly_total_losses = friendly_games.filter(loser_id=team_id).count()
            friendly_total_draws = friendly_games.filter(is_draw=True).count()

            friendly_cards_stats = FriendlyGamesPlayerGameStats.objects.filter(
                game_id__in=friendly_games.values_list('id', flat=True)
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )
            friendly_total_yellow_cards = friendly_cards_stats['total_yellow_cards'] or 0
            friendly_total_red_cards = friendly_cards_stats['total_red_cards'] or 0

            # Combine Stats
            total_games_played = tournament_total_games_played + friendly_total_games_played
            total_goals_scored = tournament_total_goals_scored + friendly_total_goals_scored
            total_goals_conceded = tournament_total_goals_conceded + friendly_total_goals_conceded
            total_assists = tournament_total_assists + friendly_total_assists
            total_wins = tournament_total_wins + friendly_total_wins
            total_losses = tournament_total_losses + friendly_total_losses
            total_draws = tournament_total_draws + friendly_total_draws
            total_yellow_cards = tournament_total_yellow_cards + friendly_total_yellow_cards
            total_red_cards = tournament_total_red_cards + friendly_total_red_cards

            # Fetch Upcoming Games where the player is in the lineup
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGameLineup.objects.filter(
                player_id=user,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = Lineup.objects.filter(
                player_id=user,
                lineup_status=Lineup.ALREADY_IN_LINEUP,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Combine the upcoming games
            upcoming_games = []

            for lineup in friendly_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            for lineup in tournament_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            # Fetch Finished Games where the player was in the lineup
            finished_games_date_filter = datetime.now()

            # Friendly Games - Finished
            friendly_finished_games = FriendlyGameLineup.objects.filter(
                player_id=user,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                game_id__game_date__lt=finished_games_date_filter.date(),
                # game_id__finish=True
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Tournament Games - Finished
            tournament_finished_games = Lineup.objects.filter(
                player_id=user,
                lineup_status=Lineup.ALREADY_IN_LINEUP,
                game_id__game_date__lt=finished_games_date_filter.date(),
                # game_id__finish=True
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Combine the finished games
            finished_games = []

            for lineup in friendly_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for lineup in tournament_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort finished games by game date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return stats and upcoming games
            return {
                "matchplayed": total_games_played,
                "win": total_wins,
                "loss": total_losses,
                "draw": total_draws,
                "goals": total_goals_scored,
                "assists": total_assists,
                "yellow_card": total_yellow_cards,
                "red": total_red_cards,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }

        except Exception as e:
            return {"status": 0, "message": "Failed to fetch player stats and upcoming games.", "error": str(e)}


    def get_coach_stats(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.COACH_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Calculate Games Stats
            tournament_total_games = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            friendly_total_games = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            total_games_played = tournament_total_games + friendly_total_games
            games_won = tournament_games_won + friendly_games_won
            games_lost = tournament_games_lost + friendly_games_lost
            games_drawn = tournament_games_drawn + friendly_games_drawn

            # Goals Conceded Calculation
            goals_conceded = (
                tournament_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            ) + (
                friendly_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            )

            # Cards Stats
            player_stats = PlayerGameStats.objects.filter(
                team_id__in=coach_branches,
                **time_filter
            )
            total_red_cards = player_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0
            total_yellow_cards = player_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0

            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_played,
                "win": games_won,
                "loss": games_lost,
                "draw": games_drawn,
                "yellow_card": total_yellow_cards,
                "red": total_red_cards,
                "goals_conceded": goals_conceded,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch coach stats.", "error": str(e)}




    def get_manager_stats(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Calculate Games Stats
            tournament_total_games = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            friendly_total_games = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            total_games_played = tournament_total_games + friendly_total_games
            games_won = tournament_games_won + friendly_games_won
            games_lost = tournament_games_lost + friendly_games_lost
            games_drawn = tournament_games_drawn + friendly_games_drawn

            # Goals Conceded Calculation
            goals_conceded = (
                tournament_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            ) + (
                friendly_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            )

            # Cards Stats
            player_stats = PlayerGameStats.objects.filter(
                team_id__in=coach_branches,
                **time_filter
            )
            total_red_cards = player_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0
            total_yellow_cards = player_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0

            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_played,
                "win": games_won,
                "loss": games_lost,
                "draw": games_drawn,
                "yellow_card": total_yellow_cards,
                "red": total_red_cards,
                "goals_conceded": goals_conceded,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch coach stats.", "error": str(e)}

    
    def get_referee_stats(self, user, time_filter=None):
        """
        Fetch referee-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the referee.
        """
        try:
            if time_filter is None:
                time_filter = {}

            # 1. Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],  # IDs representing referee roles
                **time_filter
            ).values_list('game_id', flat=True)

           

            # 2. Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

            # 3. Calculate total games officiated
            total_games_officiated = len(tournament_games_officiated) + len(friendly_games_officiated)

            # 4. Cards stats (yellow and red cards)
            cards_stats = PlayerGameStats.objects.filter(
                game_id__in=list(tournament_games_officiated) + list(friendly_games_officiated),
                **time_filter
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )


            total_yellow_cards = cards_stats['total_yellow_cards'] or 0
            total_red_cards = cards_stats['total_red_cards'] or 0
            # 5. Fetch Upcoming Games
            current_datetime = datetime.now()
            # 6. Upcoming tournament games
            upcoming_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games

            # 7. Upcoming friendly games
            upcoming_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games

            upcoming_games = []

            # 8. Format upcoming tournament games
            for game in upcoming_tournament_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            # 9. Format upcoming friendly games
            for game in upcoming_friendly_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            # 10. Fetch Finished Games
            finished_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True
            ).order_by('game_date')[:5]  # Get the last 5 finished games

            finished_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True
            ).order_by('game_date')[:5]  # Get the last 5 finished games

            finished_games = []

            # 11. Format finished tournament games
            for game in finished_tournament_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # 12. Format finished friendly games
            for game in finished_friendly_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # 13. Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_officiated,
                "yellow_card": total_yellow_cards,
                "red": total_red_cards,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games,
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch referee stats.", "error": str(e)}



    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = get_language(request)

        if user.role.id == 1:
            return redirect('Dashboard')

        # Fetch user-related data
        teams, stats = self.get_user_related_data(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "teams": teams,
            "stats": stats,
            
        }

        return render(request, "PlayerDashboard.html", context)


##############################################   LoginPage   ########################################################


class LoginPage(View):

    def authenticate_username_or_phone(self, username_or_phone, password):
        # Check if input is username or phone and retrieve user accordingly
        try:
            if username_or_phone.isdigit():
                user = User.objects.get(phone=username_or_phone)
            else:
                user = User.objects.get(username=username_or_phone)
        except User.DoesNotExist:
            return None

        # Use Django's built-in authenticate to verify the password
        user = authenticate(username=user.username, password=password)
        return user

    def get(self, request, *args, **kwargs):
        # Check if the user is already authenticated
        if request.user.is_authenticated:
            # Redirect based on user role
            if request.user.role.id == 1:
                return redirect('Dashboard')  # Redirect to the dashboard if role is 1
            else:
                return redirect('player-dashboard')  # Redirect to home for any other role

        # Proceed if user is not authenticated
        language_from_url = get_language(request)
        username_or_phone = request.COOKIES.get('username_or_phone', '')
        password = request.COOKIES.get('password', '')
        try:
            cmsdata = cms_pages.objects.get(id=12)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,   
            "username_or_phone": username_or_phone,
            "password": password,
        }

        return render(request, "login.html", context)

   
    def post(self, request, *args, **kwargs):
        # Handle language change
        language_from_url = get_language(request)

        # Fetch login type
        login_type = int(request.POST.get('login_type', 1))
        username_or_phone = request.POST.get('username_or_phone', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me', 'off') == 'on'

        # If only language is changed (no login fields are filled)
        if not username_or_phone and not password:
            cmsdata = cms_pages.objects.filter(id=12).first()
            context = {
                "current_language": language_from_url,
                "cmsdata": cmsdata,
            }
            messages.success(request, "Language changed successfully!")
            return render(request, "login.html", context)

        # Proceed with the login process
        if login_type == 1:
            user = self.authenticate_username_or_phone(username_or_phone, password)

            if user:
                if user.is_active:
                    login(request, user)

                    # If "Remember Me" is checked, set session expiration accordingly
                    if remember_me:
                        response = redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
                        response.set_cookie('username_or_phone', username_or_phone, max_age=1209600)  # 2 weeks
                        response.set_cookie('password', password, max_age=1209600)  # 2 weeks (you might want to hash this instead)
                        return response
                    else:
                        # Clear cookies if "Remember Me" is unchecked
                        response = redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
                        response.delete_cookie('username_or_phone')
                        response.delete_cookie('password')
                        return response

                    user.last_login = timezone.now()
                    user.save()
                    messages.success(request, "Login successful!")
                    return redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
                else:
                    messages.error(request, "Account is inactive.")
            else:
                messages.error(request, "Invalid credentials.")

        return redirect('login')

######################################### Forgot Password ########################################################

class ForgotPasswordPage(View):
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        context = {
            "current_language": language_from_url,
        }
        return render(request, "forgot_password.html", context)

    def post(self, request, *args, **kwargs):
        phone = request.POST.get("phone").strip()
        language_from_url = get_language(request)

        if not phone:
            messages.error(request, "Please enter a phone number.")
            return render(request, "forgot_password.html", {"current_language": language_from_url})

        user = User.objects.filter(phone=phone).first()
        if not user:
            messages.error(request, "Phone number not found.")
            return render(request, "forgot_password.html", {"current_language": language_from_url})

        # Generate and save OTP
        otp = generate_otp()
        user.otp = otp
        user.save()

        # Store phone number in session instead of URL
        request.session["reset_phone"] = phone
        request.session['language'] = language_from_url
        request.session['current_language'] = language_from_url 

        messages.success(request, f"OTP {otp} sent to your phone number.")
        return redirect("verify_forgot_password_otp")


class verify_forgot_password_otp(View):
    def get(self, request, *args, **kwargs):
        phone = request.session.get("reset_phone")
        language_from_url = get_language(request)

        # Store language in session
        request.session["language"] = language_from_url
        request.session["current_language"] = language_from_url
        request.session.save()

        if not phone:
            messages.error(request, "Session expired. Please try again.")
            return redirect("forgot_password")
        
        context = {
            "phone": phone,
            "reset_phone": phone,
            "current_language": language_from_url,
        }
        return render(request, "verify_forgot_password_otp.html", context)

    def post(self, request, *args, **kwargs):
        phone = request.session.get("reset_phone")
        otp = request.POST.get("otp")
        language_from_url = get_language(request)

        # Store language in session
        request.session["language"] = language_from_url
        request.session["current_language"] = language_from_url
        request.session.save()

        user = User.objects.filter(phone=phone, otp=otp).first()
        if not user:
            messages.error(request, "Invalid OTP. Please try again.")
            context = {
                "phone": phone,
                "current_language": language_from_url,
            }
            return render(request, "verify_forgot_password_otp.html", context)

        return redirect("reset_password")


class ResetPasswordPage(View):
    def get(self, request, *args, **kwargs):
        phone = request.session.get("reset_phone")
        language_from_url = get_language(request)

        # Store language in session
        request.session["language"] = language_from_url
        request.session["current_language"] = language_from_url
        request.session.save()

        if not phone:
            messages.error(request, "Session expired. Please try again.")
            return redirect("forgot_password")

        context = {
            "phone": phone,
            "current_language": language_from_url,
        }
        return render(request, "reset_password.html", context)

    def post(self, request, *args, **kwargs):
        language_from_url = get_language(request)

        # Store language in session
        request.session["language"] = language_from_url
        request.session["current_language"] = language_from_url
        request.session.save()

        phone = request.session.get("reset_phone")
        password = request.POST.get("password").strip()
        confirm_password = request.POST.get("confirm_password").strip()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            context = {
                "phone": phone,
                "current_language": language_from_url,
            }
            return render(request, "reset_password.html", context)

        user = User.objects.filter(phone=phone).first()
        if not user:
            messages.error(request, "Invalid phone number.")
            return redirect("forgot_password")

        # Save new password securely
        user.password = make_password(password)
        user.otp = None  # Clear OTP after successful reset
        user.save()

        # Clear session after password reset
        del request.session["reset_phone"]

        messages.success(request, "Password reset successful. Please log in.")
        return redirect("login")

########################################## Generate a random 6-digit OTP######################################################
def generate_otp():
    return str(random.randint(100000, 999999))
#################################### Register Page ##########################################
class RegisterPage(View):
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        # Fetching specific CMS data
        try:
            cmsdata = cms_pages.objects.get(id=13)
        except cms_pages.DoesNotExist:
            cmsdata = None

        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        }
        return render(request, "register.html", context)

    def post(self, request, *args, **kwargs):
        register_type = request.POST.get("register_type")
        language_from_url = get_language(request)
        
        if register_type == "1":  # Normal registration
            return self.handle_normal_registration(request)
        
        else:  # Google or Apple sign-up
            messages.error(request, "Username or phone number already exists.")
            return redirect("register")

    def handle_normal_registration(self, request):
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

        context = {
            "current_language": language_from_url,
        }

        username = request.POST.get("username")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        # Validate password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Check if username or phone already exists in the User table
        if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
            messages.error(request, "Username or phone number already exists.")
            return redirect("register")

        # Generate OTP and save user details in OTPSave table
        otp = generate_otp()
        OTPSave.objects.create(phone=phone, OTP=otp)

        # Log the OTP for development purposes

        # Store phone and username in the session to access in OTP verification
        request.session['phone'] = phone
        request.session['username'] = username
        request.session['password'] = password  # Store password in the session temporarily
        messages.success(request, "Your OTP is {}".format(otp))

        
        # Instead of passing context, include language as GET parameter
        return redirect(f"{reverse('verify_otp')}?Language={language_from_url}")
#################################### OTP Verification #######################################
class OTPVerificationView(View):
    def get(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        context = {
            "current_language":language_from_url,
        }

        return render(request, "otp_verification.html",context)

    def post(self, request, *args, **kwargs):
        language_from_url = get_language(request)
        context = {
            "current_language":language_from_url,
        }
        otp_input = request.POST.get("otp")

        # Retrieve the saved username and phone from the session
        username = request.session.get('username')
        phone = request.session.get('phone')
        password = request.session.get('password')  # Retrieve password from session
        email = request.session.get('email')  # Retrieve password from session

        try:
            otp_record = OTPSave.objects.get(OTP=otp_input, phone=phone)
        except OTPSave.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("verify_otp")

        # If OTP is valid, create a new user in the User table
        user = User.objects.create(
            username=username,
            phone=phone,
            email=email,  # Make sure to handle email properly
            role_id=5,
        )
        user.set_password(password)  # Use the password stored in the session
        user.save()

        # Delete the OTP record now that the user is registered
        otp_record.delete()

        # Clear session data
        request.session.pop('username', None)
        request.session.pop('password', None)
        request.session.pop('phone', None)

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")


def custom_404_view(request, exception=None):
        # template_name = "Admin/User/Referee_List.html"
    

        return render(request, 'templates/404.html')

class UserInfoUpdateView(View):
    template_name = 'user_info.html'
    success_url = reverse_lazy('verify_otp')
    login_url = reverse_lazy('google_auth')  # Redirect to Google Auth if not logged in
    model = User
    form_class = UserInfoForm
    template_name = 'user_info.html'
    success_url = reverse_lazy('verify_otp')

    def get_initial(self):
        initial = super().get_initial()
        email = self.request.session.get('email')  # Retrieve email from session
        if email:
            initial['email'] = email
        return initial
    
    def get(self, request, *args, **kwargs):
        form = UserInfoForm()  # Instantiate the form
        email = request.session.get('email', '')
        
        # Use the get_language function to retrieve and update language
        language_from_url = get_language(request)

        # Setting the language context for the template
        context = {
            "current_language": language_from_url,
        }

        # If email exists in the session, set it as the initial value in the form
        if email:
            form.initial['email'] = email

        return render(request, self.template_name, {'form': form, **context})
    
    def post(self, request, *args, **kwargs):
        form = UserInfoForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            role = Role.objects.get(id=5)  # Fetch Role instance with ID 5
            user.role = role

            # Retrieve form data
            phone = form.cleaned_data.get('phone')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Use the get_language function to retrieve and update language
            language_from_url = get_language(request)

            # Validate if the username is already taken
            if User.objects.filter(username=username).exists():
                form.add_error('username', "This username is already taken. Please try a different username.")
                return render(request, self.template_name, {'form': form})

            if User.objects.filter(phone=phone).exists():
                messages.error(request, "This phone number is already registered. Please try a different number.")
                return redirect("user_info_update")

            # Generate OTP and save it
            otp = generate_otp()
            OTPSave.objects.update_or_create(
                phone=phone,
                defaults={'OTP': otp}
            )

            request.session['phone'] = phone
            request.session['username'] = username
            request.session['email'] = email

            messages.success(request, f"Your OTP is {otp}")
            return redirect(f"{reverse_lazy('google_verify_otp')}?Language={language_from_url}")
        else:
            # Display form-specific errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")

            return render(request, self.template_name, {'form': form})

class googleOTPVerificationView(View):
    def get(self, request, *args, **kwargs):
        # Use the get_language function to retrieve and update language
        language_from_url = get_language(request)

        context = {
            "current_language": language_from_url,
        }

        return render(request, "otp_verification.html", context)

    def post(self, request, *args, **kwargs):
        # Use the get_language function to retrieve and update language
        language_from_url = get_language(request)

        otp_input = request.POST.get("otp")

        # Retrieve session data
        username = request.session.get('username')
        phone = request.session.get('phone')
        email = request.session.get('email')

        if not all([username, phone, email]):
            messages.error(request, "Missing session data, please try again.")
            return redirect("user_info_update")

        # Validate email, phone, and username
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered. Please try a different email.")
            return redirect("user_info_update")
        
        if User.objects.filter(phone=phone).exists():
            messages.error(request, "This phone number is already registered. Please try a different number.")
            return redirect("user_info_update")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken. Please try a different username.")
            return redirect("user_info_update")
        
        if Team.objects.filter(team_username=username).exists():
            messages.error(request, "This username is already taken by a team. Please try a different username.")
            return redirect("user_info_update")
        
        if TrainingGroups.objects.filter(group_username=username).exists():
            messages.error(request, "This username is already taken by a training group. Please try a different username.")
            return redirect("user_info_update")

        try:
            otp_record = OTPSave.objects.get(OTP=otp_input, phone=phone)
        except OTPSave.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("google_verify_otp")

        # Create user if OTP is valid
        password = f"{username}@{phone}"  # Concatenate username and phone with '@' symbol
        user = User.objects.create(
            username=username,
            phone=phone,
            email=email,
            role_id=5,
        )
        user.set_password(password)  # Set the password securely
        user.save()

        # Delete OTP record
        otp_record.delete()

        # Clear session data
        request.session.pop('username', None)
        request.session.pop('password', None)
        request.session.pop('phone', None)
        request.session.pop('email', None)

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")


class GoogleAuthView(View):
    def get(self, request):
        # Use the get_language function to retrieve and update language
        language_from_url = get_language(request)

        # Google OAuth 2.0 URL
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        scope = "email"
        auth_url = (
            "https://accounts.google.com/o/oauth2/auth"
            f"?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
        )
        return redirect(auth_url)


class GoogleCallbackView(View):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return JsonResponse({"error": "Authorization code not provided"}, status=400)
        language_from_url = get_language(request)
        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        token_response = requests.post(token_url, data=data)
        token_json = token_response.json()

        if "access_token" not in token_json:
            return JsonResponse({"error": "Failed to retrieve access token", "details": token_json}, status=400)

        access_token = token_json["access_token"]

        # Use the access token to retrieve the user's email
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        user_info_json = user_info_response.json()

        email = user_info_json.get("email")
        if not email:
            return JsonResponse({"error": "Failed to retrieve email"}, status=400)

        user = User.objects.filter(email=email).first()
        if user:
            login(request, user)  # Assuming you have Django's authentication set up
            messages.success(request, "Welcome back!")
            return redirect("player-dashboard")  # Or wherever you want to redirect after login

        request.session['email'] = email
        request.session.save()  # Explicitly save the session to persist email

        return HttpResponseRedirect(f"{reverse_lazy('user_info_update')}?Language={language_from_url}")

###################### Apple Login and Signup #########################################################
class AppleAuthView(View):
    def get(self, request):
        # Get language from URL or session
        language_from_url = request.GET.get('Language', None)
        if language_from_url:
            request.session['language'] = language_from_url
        else:
            language_from_url = request.session.get('language', 'en')

        # Generate the Apple Sign-In URL
        client_id = os.getenv("APPLE_CLIENT_ID")
        redirect_uri = os.getenv("APPLE_REDIRECT_URI")
        scope = "name email"
        response_mode = "form_post" 

        auth_url = (
            f"https://appleid.apple.com/auth/authorize?"
            f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_mode={response_mode}"
        )
        return redirect(auth_url)

@method_decorator(csrf_exempt, name='dispatch')
class AppleCallbackView(View):
    def post(self, request):
        code = request.POST.get('code')
        if not code:
            return JsonResponse({"error": "Authorization code not provided"}, status=400)

        return self.handle_auth_callback(request, code)

    def handle_auth_callback(self, request, code):
        # Get language from session
        language_from_url = get_language(request)

        # Generate client secret
        private_key = os.getenv("APPLE_PRIVATE_KEY")
        # Ensure the key is formatted correctly by stripping unwanted whitespace
        private_key = private_key.strip()
        client_id = os.getenv("APPLE_CLIENT_ID")
        team_id = os.getenv("APPLE_TEAM_ID")
        key_id = os.getenv("APPLE_KEY_ID")
        redirect_uri = os.getenv("APPLE_REDIRECT_URI")

        current_time = int(time.time())
        claims = {
            "iss": team_id,
            "iat": current_time,
            "exp": current_time + 3600,  # Token valid for 1 hour
            "aud": "https://appleid.apple.com",
            "sub": client_id,
        }

        client_secret = jwt.encode(
            claims,
            private_key,
            algorithm="ES256",
            headers={"kid": key_id},
        )

        # Exchange the authorization code for tokens
        token_url = "https://appleid.apple.com/auth/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        token_response = requests.post(token_url, data=data)
        token_json = token_response.json()

        if "id_token" not in token_json:
            return JsonResponse({"error": "Failed to retrieve tokens", "details": token_json}, status=400)

        # Decode the ID token to get the user's information
        id_token = token_json["id_token"]
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        email = decoded_token.get("email")

        if not email:
            return JsonResponse({"error": "Failed to retrieve email from ID token"}, status=400)

        # Check if the email is already registered
        user = User.objects.filter(email=email).first()
        if user:
            # If user exists, log them in
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect("player-dashboard")
        # Save the email in the session
        request.session['email'] = email
        request.session['language'] = language_from_url
        request.session.save()  # Explicitly save the session to persist email and language

        # Redirect after saving email
        return HttpResponseRedirect(f"{reverse_lazy('user_info_update')}?Language={language_from_url}")

######################## User Dashboard For Games #########################################################
class UserDashboardGames(LoginRequiredMixin,View):

    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

        # Fetch user-related data
        stats = self.get_user_dashboard_games(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "stats": stats,
            
        }

        return render(request, "PlayerDashboardGames.html", context)

    
    def get_user_dashboard_games(self, user, time_filter=None):
        """
        Fetch user-related data such as event bookings, teams, stats, and upcoming/latest games
        based on the user's role.
        """

        stats = {
                "upcoming_games": [],
                "finished_games": [],
            }
        # Fetch upcoming games based on the user's role
        if user.role.id == 2:  # Player role
            stats = self.get_player_games(user, time_filter)
        elif user.role.id == 3:  # Coach role
            stats = self.get_coach_games(user, time_filter)
        elif user.role.id == 4:  # Referee role
            stats = self.get_referee_games(user, time_filter)
        elif user.role.id == 6:  # Manager role
            stats = self.get_manager_games(user, time_filter)

        return stats

    from datetime import datetime

    def get_manager_games(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

           
            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            )

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            )

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            )

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            )

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch Manager stats.", "error": str(e)}


    def get_referee_games(self, user, time_filter=None):
        """
        Fetch referee-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the referee.
        """
        try:
            if time_filter is None:
                time_filter = {}

            # Check if the user is an official in any game (official types 2, 3, 4, 5)
            is_official = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5]
            ).exists() or FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5]
            ).exists()

            # If the user is not an official for any game, return an appropriate message
            if not is_official:
                return {"status": 0, "message": "User is not an official for any game."}

            # Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],  # IDs representing referee roles
                **time_filter
            ).values_list('game_id', flat=True)

            # Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Upcoming tournament games
            upcoming_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False  # Ensure the game is not finished
            ).order_by('game_date')

            # Upcoming friendly games
            upcoming_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False  # Ensure the game is not finished
            ).order_by('game_date')

            upcoming_games = []

            for game in upcoming_tournament_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            for game in upcoming_friendly_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            # Fetch Finished Games
            finished_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True  # Ensure the game is finished
            ).order_by('game_date')

            finished_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True  # Ensure the game is finished
            ).order_by('game_date')

            finished_games = []

            for game in finished_tournament_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in finished_friendly_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games,
            }

        except Exception as e:
            return {"status": 0, "message": "Failed to fetch referee stats.", "error": str(e)}

    


    def get_player_games(self, user, time_filter): 
        """
        Fetch upcoming and finished games where the player (role 2) is already in the lineup.
        """
        try:
            # Fetch the team the player is associated with
            team = JoinBranch.objects.filter(user_id=user.id).first()
            if not team:
                return {"status": 0, "message": "User is not associated with any team."}

            # Ensure time_filter is valid
            time_filter = time_filter or {}

            # Fetch upcoming and finished games where the player is in the lineup
            current_datetime = datetime.now()
            upcoming_games = []
            finished_games = []
            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGameLineup.objects.filter(
                player_id=user.id,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id')

            # Tournament Games - Upcoming
            tournament_upcoming_games = Lineup.objects.filter(
                player_id=user.id,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id')

            # Combine the upcoming games
            
            for lineup in friendly_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date.strftime("%Y-%m-%d"),
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            for lineup in tournament_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date.strftime("%Y-%m-%d"),
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            # Fetch finished games where the player was in the lineup
            finished_games_date_filter = datetime.now()

            # Friendly Games - Finished
            friendly_finished_games = FriendlyGameLineup.objects.filter(
                player_id=user.id,
                game_id__game_date__lt=finished_games_date_filter.date(),
                game_id__finish=True
            ).select_related('game_id', 'team_id')

            # Tournament Games - Finished
            tournament_finished_games = Lineup.objects.filter(
                player_id=user.id,
                game_id__game_date__lt=finished_games_date_filter.date(),
                game_id__finish=True
            ).select_related('game_id', 'team_id')

            # Combine the finished games
            

            for lineup in friendly_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date.strftime("%Y-%m-%d"),
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}" if game.team_a_goal is not None and game.team_b_goal is not None else "TBD",
                })

            for lineup in tournament_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                    "game_date": game.game_date.strftime("%Y-%m-%d"),
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}" if game.team_a_goal is not None and game.team_b_goal is not None else "TBD",
                })

            # Sort finished games by game date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return stats and upcoming games
            return {
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }

        except Exception as e:
            return {"status": 0, "message": "Failed to fetch player games.", "error": str(e)}

        
    def get_coach_games(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.COACH_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

           
            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            )

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            )

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            )

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            )

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch coach stats.", "error": str(e)}
        

class UserEventBookingInfo(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

        # Fetch user-related data
        events = self.get_user_event_bookings(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "events": events,
        }

        return render(request, "PlayerDashboardEvents.html", context)


    def get_user_event_bookings(self, user):
        """
        Fetches events booked by the user along with the relevant details.
        """
        bookings = EventBooking.objects.filter(created_by_id=user.id).order_by('-event__event_date')
        events = []
        for booking in bookings:
            event = booking.event
            events.append({
                'event_name': event.event_name,
                'event_type': event.event_type.name_en,
                'tickets': booking.tickets,
                'ticket_amount': booking.ticket_amount,
                'total_amount': booking.total_amount,
                'event_date': event.event_date,
            })
        return events
    
class UserCreatedFieldsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')        # Fetch fields created by the current user
        fields = Field.objects.filter(user_id=user)
        
        # Prepare the data
        fields_data = []
        for field in fields:
            fields_data.append({
                'field_name': field.field_name,
                'image': field.image.url if field.image else None,
                'field_capacity': field.field_capacity.name if field.field_capacity else None,  # Assuming `FieldCapacity` has a `name` attribute
                'ground_type': field.ground_type.name_en if field.ground_type else None,  # Assuming `GroundMaterial` has a `name` attribute
                'country_id': field.country_id.name if field.country_id else None,  # Assuming `Country` has a `name` attribute
                'city_id': field.city_id.name if field.city_id else None,  # Assuming `City` has a `name` attribute
            })
        
        context = {
            'fields': fields_data,
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
        }
        return render(request, 'PlayerDashboardFields.html', context)



#################### User Training List of Dashboard #############################
class UserDashboardTrainings(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

        # Fetch user-related training data
        stats = self.get_user_dashboard_trainings(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "created_trainings": stats.get('created_trainings'),
            "joined_trainings": stats.get('joined_trainings'),
        }

        return render(request, "PlayerDashboardTraining.html", context)

    def get_user_dashboard_trainings(self, user):
        """
        Fetch user-related training data based on the user's role.
        For Player role, return both joined and created trainings.
        For other roles, return only created trainings.
        """
        stats = {
                "joined_trainings": [],
                "created_trainings": [],
            }

        # For Player role (id == 2), fetch both joined and created trainings
        if user.role.id == 2:  # Player role
            stats["joined_trainings"] = self.get_joined_trainings(user)
            stats["created_trainings"] = self.get_created_trainings(user)
        else:  # For other roles, fetch only created trainings
            stats["created_trainings"] = self.get_created_trainings(user)

        return stats

    def get_joined_trainings(self, user):
        """
        Get the trainings that the user has joined. This calls the `MyJoinedTrainingsView` logic.
        """
        joined_trainings = Training_Joined.objects.filter(user=user).select_related('training')
        
        if not joined_trainings.exists():
            return []

        # Extract and return the training sessions
        trainings = [entry.training for entry in joined_trainings]
        return sorted(trainings, key=lambda x: x.training_date, reverse=True)

    def get_created_trainings(self, user):
        """
        Get the trainings created by the user. This calls the `MyTrainingsView` logic.
        """
        created_trainings = Training.objects.filter(created_by_id=user.id)
        accessible_trainings = [training for training in created_trainings if self._has_access(training, user)]
        return sorted(accessible_trainings, key=lambda t: t.training_date, reverse=True)

    def _has_access(self, training, user):
        """
        Helper function to check if the user has access to the given training.
        This is a simplified version of the logic from the `MyTrainingsView`.
        """
        if training.creator_type == 1:  # USER_TYPE
            if training.created_by_id == user.id:  # Creator is the same user
                return True

            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branches = JoinBranch.objects.filter(user_id=user.id).values_list('branch_id', flat=True)

            if not creator_branches or not user_branches:
                return False

            if any(branch in user_branches for branch in creator_branches):
                return True
        elif training.creator_type == 2:  # TEAM_TYPE
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user.id:  # User is the team founder
                return True

        return False





############################### SearchView ########################


class SearchView(View):
    def get(self, request, *args, **kwargs):
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')
        query = request.GET.get('q', '')
        
        # Filter results based on the query
        user_results = User.objects.filter(Q(username__icontains=query) & ~Q(role=1)) if query else []
        team_results = Team.objects.filter(team_name__icontains=query) if query else []
        team_branch_results = TeamBranch.objects.filter(team_name__icontains=query) if query else []

        # Create context to pass to the template
        context = {
            'query': query,
            'user_results': user_results,
            'team_results': team_results,
            'team_branch_results': team_branch_results,
            'current_language':language_from_url
        }

        # Render the template with the context data
        return render(request, 'search.html', context)
    


class TeamPageSearchResults(View):
    def get_team_related_data(self, team):
        # Get branches sorted alphabetically by team_name
        branches = TeamBranch.objects.filter(team_id=team).order_by('team_name')

        # Get sponsors sorted alphabetically by name
        sponsors = Sponsor.objects.filter(created_by_id=team.id, creator_type=2).order_by('name')

        # Get the latest 5 events (ordered by date, assuming `event_date` is the field for event date)
        events = Event.objects.filter(created_by_id=team.id, creator_type=2).order_by('-event_date')[:5]

        # Calculate ticket sales for each event
        events_with_sales = []
        for event in events:
            total_tickets_sold = (
                EventBooking.objects.filter(event=event).aggregate(
                    total=Sum("tickets")
                )["total"]
                or 0
            )
            events_with_sales.append(
                {"event": event, "total_tickets_sold": total_tickets_sold}
            )

        return branches, sponsors, events_with_sales

    def get(self, request, *args, **kwargs):
        # Language handling
        language_from_url = request.GET.get('Language', None)
        if language_from_url:
            request.session['language'] = language_from_url
        else:
            language_from_url = request.session.get('language', 'en')

        # Fetch the team_id from GET parameters
        team_id = request.GET.get("team_id")
        if not team_id:
            messages.error(request, "Team ID is missing. Please provide a valid team.")
            return redirect("Dashboard")

        try:
            # Get the team object based on team_id
            team = Team.objects.get(id=team_id)

            # Fetch the required related data
            branches, sponsors, events_with_sales = self.get_team_related_data(team)

            # Add team data to the context
            context = {
                "team": team,
                "branches": branches,
                "sponsors": sponsors,
                "events_with_sales": events_with_sales,
                'current_language': language_from_url,
            }

        except Team.DoesNotExist:
            messages.error(request, "The specified team was not found.")
            return redirect("index")

        # Render the template with the updated context
        return render(request, 'team/teampage.html', context)




class PlayerInfoPage(View):
    
    def get_user_related_data(self, user, time_filter=None):
        """
        Fetch user-related data such as event bookings, teams, stats, and upcoming/latest games
        based on the user's role.
        """
        # Fetch event bookings
        # Fetch teams associated with the user
        teams = JoinBranch.objects.filter(user_id=user.id)

        # Initialize stats
        stats = {}

        # Fetch upcoming games based on the user's role
        if user.role.id == 2:  # Player role
            stats = self.get_player_stats(user, time_filter)
        elif user.role.id == 3:  # Coach role
            stats = self.get_coach_stats(user, time_filter)
        elif user.role.id == 4:  # Referee role
            stats = self.get_referee_stats(user, time_filter)
        elif user.role.id == 6:  # Manager role
            stats = self.get_manager_stats(user, time_filter)


        return teams, stats

    def get_player_stats(self, user, time_filter):
        """
        Fetch player-specific stats, including total wins, losses, draws, games played, goals, assists, and cards
        from both tournament and friendly games, and also return the upcoming games where the player is already in the lineup.
        """
        try:
            # Fetch the team the player is associated with
            team = JoinBranch.objects.filter(user_id=user.id).first()
            if not team:
                return {"status": 0, "message": "User is not associated with any team."}

            team_id = team.branch_id

            # Ensure time_filter is valid
            time_filter = time_filter or {}

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                (Q(team_a=team_id) | Q(team_b=team_id)),
                finish=True,
                **time_filter
            )
            tournament_total_games_played = tournament_games.count()

            tournament_goals = tournament_games.aggregate(
                total_goals_a=Sum('team_a_goal'),
                total_goals_b=Sum('team_b_goal')
            )
            tournament_total_goals_scored = tournament_goals['total_goals_a'] or 0
            tournament_total_goals_conceded = tournament_goals['total_goals_b'] or 0

            tournament_total_assists = PlayerGameStats.objects.filter(
                game_id__in=tournament_games.values_list('id', flat=True)
            ).aggregate(
                total_assists=Sum('assists')
            )['total_assists'] or 0

            tournament_total_wins = tournament_games.filter(winner_id=team_id).count()
            tournament_total_losses = tournament_games.filter(loser_id=team_id).count()
            tournament_total_draws = tournament_games.filter(is_draw=True).count()

            tournament_cards_stats = PlayerGameStats.objects.filter(
                game_id__in=tournament_games.values_list('id', flat=True)
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )
            tournament_total_yellow_cards = tournament_cards_stats['total_yellow_cards'] or 0
            tournament_total_red_cards = tournament_cards_stats['total_red_cards'] or 0

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                (Q(team_a=team_id) | Q(team_b=team_id)),
                finish=True,
                **time_filter
            )
            friendly_total_games_played = friendly_games.count()

            friendly_goals = friendly_games.aggregate(
                total_goals_a=Sum('team_a_goal'),
                total_goals_b=Sum('team_b_goal')
            )
            friendly_total_goals_scored = friendly_goals['total_goals_a'] or 0
            friendly_total_goals_conceded = friendly_goals['total_goals_b'] or 0

            friendly_total_assists = FriendlyGamesPlayerGameStats.objects.filter(
                game_id__in=friendly_games.values_list('id', flat=True)
            ).aggregate(
                total_assists=Sum('assists')
            )['total_assists'] or 0

            friendly_total_wins = friendly_games.filter(winner_id=team_id).count()
            friendly_total_losses = friendly_games.filter(loser_id=team_id).count()
            friendly_total_draws = friendly_games.filter(is_draw=True).count()

            friendly_cards_stats = FriendlyGamesPlayerGameStats.objects.filter(
                game_id__in=friendly_games.values_list('id', flat=True)
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )
            friendly_total_yellow_cards = friendly_cards_stats['total_yellow_cards'] or 0
            friendly_total_red_cards = friendly_cards_stats['total_red_cards'] or 0

            # Combine Stats
            total_games_played = tournament_total_games_played + friendly_total_games_played
            total_goals_scored = tournament_total_goals_scored + friendly_total_goals_scored
            total_goals_conceded = tournament_total_goals_conceded + friendly_total_goals_conceded
            total_assists = tournament_total_assists + friendly_total_assists
            total_wins = tournament_total_wins + friendly_total_wins
            total_losses = tournament_total_losses + friendly_total_losses
            total_draws = tournament_total_draws + friendly_total_draws
            total_yellow_cards = tournament_total_yellow_cards + friendly_total_yellow_cards
            total_red_cards = tournament_total_red_cards + friendly_total_red_cards

            # Fetch Upcoming Games where the player is in the lineup
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGameLineup.objects.filter(
                player_id=user,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = Lineup.objects.filter(
                player_id=user,
                lineup_status=Lineup.ALREADY_IN_LINEUP,
                game_id__game_date__gte=current_datetime.date(),
                game_id__finish=False
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Combine the upcoming games
            upcoming_games = []

            for lineup in friendly_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            for lineup in tournament_upcoming_games:
                game = lineup.game_id
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            # Fetch Finished Games where the player was in the lineup
            finished_games_date_filter = datetime.now()

            # Friendly Games - Finished
            friendly_finished_games = FriendlyGameLineup.objects.filter(
                player_id=user,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                game_id__game_date__lt=finished_games_date_filter.date(),
                # game_id__finish=True
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Tournament Games - Finished
            tournament_finished_games = Lineup.objects.filter(
                player_id=user,
                lineup_status=Lineup.ALREADY_IN_LINEUP,
                game_id__game_date__lt=finished_games_date_filter.date(),
                # game_id__finish=True
            ).select_related('game_id', 'team_id').order_by('game_id__game_date')[:5]

            # Combine the finished games
            finished_games = []

            for lineup in friendly_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for lineup in tournament_finished_games:
                game = lineup.game_id
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort finished games by game date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return stats and upcoming games
            return {
                "matchplayed": total_games_played,
                "win": total_wins,
                "loss": total_losses,
                "draw": total_draws,
                "goals": total_goals_scored,
                "assists": total_assists if total_assists is not None else 0,
                "yellow_card": total_yellow_cards if total_yellow_cards is not None else 0,
                "red": total_red_cards if total_red_cards is not None else 0,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }

        except Exception as e:
            return {"status": 0, "message": "Failed to fetch player stats and upcoming games.", "error": str(e)}


    def get_coach_stats(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.COACH_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Calculate Games Stats
            tournament_total_games = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            friendly_total_games = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            total_games_played = tournament_total_games + friendly_total_games
            games_won = tournament_games_won + friendly_games_won
            games_lost = tournament_games_lost + friendly_games_lost
            games_drawn = tournament_games_drawn + friendly_games_drawn

            # Goals Conceded Calculation
            goals_conceded = (
                tournament_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            ) + (
                friendly_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            )

            # Cards Stats
            player_stats = PlayerGameStats.objects.filter(
                team_id__in=coach_branches,
                **time_filter
            )
            total_red_cards = player_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0
            total_yellow_cards = player_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0

            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_played,
                "win": games_won,
                "loss": games_lost,
                "draw": games_drawn,
                "yellow_card": total_yellow_cards if total_yellow_cards is not None else 0,
                "red": total_red_cards if total_red_cards is not None else 0,
                "goals_conceded": goals_conceded,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch coach stats.", "error": str(e)}




    def get_manager_stats(self, user, time_filter=None):
        """
        Fetch coach-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the coach's branches.
        """
        try:
            # Default time_filter to an empty dictionary if None
            if time_filter is None:
                time_filter = {}

            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament Games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Friendly Games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )

            # Calculate Games Stats
            tournament_total_games = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            friendly_total_games = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            total_games_played = tournament_total_games + friendly_total_games
            games_won = tournament_games_won + friendly_games_won
            games_lost = tournament_games_lost + friendly_games_lost
            games_drawn = tournament_games_drawn + friendly_games_drawn

            # Goals Conceded Calculation
            goals_conceded = (
                tournament_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            ) + (
                friendly_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            )

            # Cards Stats
            player_stats = PlayerGameStats.objects.filter(
                team_id__in=coach_branches,
                **time_filter
            )
            total_red_cards = player_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0
            total_yellow_cards = player_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0

            # Fetch Upcoming Games
            current_datetime = datetime.now()

            # Friendly Games - Upcoming
            friendly_upcoming_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            # Tournament Games - Upcoming
            tournament_upcoming_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_id__game_date')[:5]

            upcoming_games = []

            for game in friendly_upcoming_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            for game in tournament_upcoming_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo":game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            # Fetch Finished Games
            friendly_finished_games = friendly_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            tournament_finished_games = tournament_games.filter(
                game_date__lt=current_datetime.date(),
                finish=True
            ).order_by('game_id__game_date')[:5]

            finished_games = []

            for game in friendly_finished_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            for game in tournament_finished_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_played,
                "win": games_won,
                "loss": games_lost,
                "draw": games_drawn,
                "yellow_card": total_yellow_cards if total_yellow_cards is not None else 0,
                "red": total_red_cards if total_red_cards is not None else 0,
                "goals_conceded": goals_conceded,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games
            }
        
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch coach stats.", "error": str(e)}

    
    def get_referee_stats(self, user, time_filter=None):
        """
        Fetch referee-specific stats, including stats for tournament and friendly games,
        and return upcoming and finished games for the referee.
        """
        try:
            if time_filter is None:
                time_filter = {}

            # 1. Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],  # IDs representing referee roles
                **time_filter
            ).values_list('game_id', flat=True)

            # 2. Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

        

            # 3. Calculate total games officiated
            total_games_officiated = len(tournament_games_officiated) + len(friendly_games_officiated)

           

            # 4. Cards stats (yellow and red cards)
            cards_stats = PlayerGameStats.objects.filter(
                game_id__in=list(tournament_games_officiated) + list(friendly_games_officiated),
                **time_filter
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )

           

            total_yellow_cards = cards_stats['total_yellow_cards'] or 0
            total_red_cards = cards_stats['total_red_cards'] or 0

            # 5. Fetch Upcoming Games
            current_datetime = datetime.now()

           

            # 6. Upcoming tournament games
            upcoming_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games


            # 7. Upcoming friendly games
            upcoming_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games

        
            upcoming_games = []

            # 8. Format upcoming tournament games
            for game in upcoming_tournament_games:
                upcoming_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_start_time": game.game_start_time,
                    "game_end_time": game.game_end_time,
                })

            # 9. Format upcoming friendly games
            for game in upcoming_friendly_games:
                upcoming_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                })

            # 10. Fetch Finished Games
            finished_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True
            ).order_by('game_date')[:5]  # Get the last 5 finished games

            finished_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True
            ).order_by('game_date')[:5]  # Get the last 5 finished games

            finished_games = []

            # 11. Format finished tournament games
            for game in finished_tournament_games:
                finished_games.append({
                    "game_type": game.tournament_id.tournament_name,
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # 12. Format finished friendly games
            for game in finished_friendly_games:
                finished_games.append({
                    "game_type": "Friendly",
                    "team_a_vs_team_b": f"{game.team_a}    VS    {game.team_b}",
                    "game_date": game.game_date,
                    "game_start_time": game.game_start_time,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a.team_id.team_logo else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b.team_id.team_logo else None,
                    "game_end_time": game.game_end_time,
                    "score": f"{game.team_a_goal} - {game.team_b_goal}",
                })

            # 13. Sort Finished Games by Date
            finished_games = sorted(finished_games, key=lambda x: x["game_date"], reverse=True)

            # Return the stats
            return {
                "matchplayed": total_games_officiated,
                "yellow_card": total_yellow_cards if total_yellow_cards is not None else 0,
                "red": total_red_cards if total_red_cards is not None else 0,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games,
            }
        except Exception as e:
            return {"status": 0, "message": "Failed to fetch referee stats.", "error": str(e)}


    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')  # Fetch user_id from query parameters
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('search')

        # Handle language from URL or session
        language_from_url = request.GET.get('Language', None)
        if language_from_url:
            # Save language to the session if it's provided in the URL
            request.session['language'] = language_from_url
        else:
            # Fallback to the session's language or default to 'en'
            language_from_url = request.session.get('language', 'en')

        if user.role.id == 1:
            return redirect('Dashboard')

        # Fetch user-related data
        teams, stats = self.get_user_related_data(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "teams": teams,
            "stats": stats,
            "infouser": user,
        }

        return render(request, "PlayerInfo.html", context)

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('search')
        language_from_url = request.GET.get('Language', None)
        
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

        if user.role.id == 1:
            return redirect('Dashboard')

        # Fetch user-related data
        teams, stats = self.get_user_related_data(user)
        context = {
            "current_language": language_from_url,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "teams": teams,
            "stats": stats,
            "infouser":user,
            
        }

        return render(request, "PlayerInfo.html", context)

  
class TeamDetailsView(View):

    def get_team_data(self, team):
        # 1. Get staff members from JoinBranch where role is 1, 2, or 3
        staff_members = JoinBranch.objects.filter(
            branch_id=team, 
            joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE, JoinBranch.MEDICAL_STAFF_TYPE]
        ).order_by('id')

        # 2. Get players from JoinBranch where role is 4
        players = JoinBranch.objects.filter(
            branch_id=team, 
            joinning_type=JoinBranch.PLAYER_TYPE
        ).order_by('id')

        # 3. Get joined tournaments from TournamentGroupTeam where status is 1
        joined_tournaments = TournamentGroupTeam.objects.filter(
            team_branch_id=team, 
            status=TournamentGroupTeam.ACCEPTED
        ).order_by('-created_at')[:5]

        # 4. Get finished friendly games
        friendly_games = FriendlyGame.objects.filter(
            Q(team_a=team) | Q(team_b=team), 
            # finish=True
        ).order_by('-game_date')

        # 5. Get finished tournament games
        tournament_games = TournamentGames.objects.filter(
            Q(team_a=team) | Q(team_b=team), 
            # finish=True
        ).order_by('-game_date')

        # Combine friendly and tournament games
        combined_games = sorted(
            chain(friendly_games, tournament_games),  # Merge querysets
            key=lambda game: game.game_date,  # Sort by date
            reverse=True  # Show latest games first
        )[:5]

        # Calculate stats
        total_wins = 0
        total_losses = 0
        total_draws = 0
        total_goals_scored = 0
        total_goals_conceded = 0

        # Process combined games
        finished_games = []
        for game in combined_games:
            # Determine if it's a Friendly or Tournament Game
            if isinstance(game, FriendlyGame):
                game_type = "Friendly"
                tournament_name = "N/A"
                group_name = "N/A"
            else:
                game_type = "Tournament"
                tournament_name = game.tournament_id.tournament_name if game.tournament_id else "N/A"
                group_name = game.group_id.group_name if game.group_id else "N/A"

            # Calculate statistics
            if game.winner_id == str(team.id):
                total_wins += 1
            elif game.loser_id == str(team.id):
                total_losses += 1
            elif game.is_draw:
                total_draws += 1

            # Goals scored and conceded
            if game.team_a == team:
                total_goals_scored += game.team_a_goal or 0
                total_goals_conceded += game.team_b_goal or 0
            else:
                total_goals_scored += game.team_b_goal or 0
                total_goals_conceded += game.team_a_goal or 0

            # Append game data
            finished_games.append({
                "game_type": game_type,
                "tournament_name": tournament_name,
                "game_number": game.game_number,
                "game_date": game.game_date,
                "game_start_time": game.game_start_time,
                "game_end_time": game.game_end_time,
                "group_name": group_name,
                "team_a_vs_team_b": f"{game.team_a} VS {game.team_b}",
                "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id.team_logo else None,
                "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id.team_logo else None,
                "score": f"{game.team_a_goal or 0} - {game.team_b_goal or 0}",
            })

        # Stats for all games combined
        stats = {
            "wins": total_wins,
            "losses": total_losses,
            "draws": total_draws,
            "goals_scored": total_goals_scored,
            "goals_conceded": total_goals_conceded,
            "games_played": len(combined_games),  # Total games played
        }

        return staff_members, players, joined_tournaments, finished_games, stats



    def get(self, request, *args, **kwargs):
        # Handle language selection
        language_from_url = request.GET.get('Language', None)
        if language_from_url:
            # Save to session if found in URL
            request.session['language'] = language_from_url
        else:
            # Use session language or default to 'en'
            language_from_url = request.session.get('language', 'en')

        # Fetch the team_id from GET parameters
        team_id = request.GET.get("team_id")
        if not team_id:
            messages.error(request, "Team ID is missing. Please provide a valid team.")
            return redirect("Dashboard")

        try:
            # Get the team object based on team_id
            team = TeamBranch.objects.get(id=team_id)

            # Fetch the required related data
            staff_members, players, joined_tournaments, finished_games, stats = self.get_team_data(team)

            # Add team data to the context
            context = {
                "team": team,
                "staff_members": staff_members,
                "players": players,
                "joined_tournaments": joined_tournaments,
                "finished_games": finished_games,
                "stats": stats,  # Add stats to context
                'current_language': language_from_url,  # Add language to context
            }

        except TeamBranch.DoesNotExist:
            messages.error(request, "The specified team was not found.")
            return redirect("index")

        # Render the template with the updated context
        return render(request, 'team/team.html', context)


class TeamPageDashboard(LoginRequiredMixin, View):
    template_name = 'PlayerDashboardTeamPage.html'

    def get(self, request, *args, **kwargs):
        # Handle language selection
        language_from_url = request.GET.get('Language', None)
        if language_from_url:
            # Save to session if found in URL
            request.session['language'] = language_from_url
        else:
            # Use session language or default to 'en'
            language_from_url = request.session.get('language', 'en')

        user = request.user
        user_id = user.id
        
        try:
            # Attempt to fetch the team
            team = Team.objects.get(team_founder=user_id)

            # Prepare context data
            context = {
                'team': team,
                'current_language': language_from_url,  # Add language to context
                'user': user,
                "cmsdata": cms_pages.objects.filter(id=14).first(),
            }
            return render(request, self.template_name, context)

        except Team.DoesNotExist:
            # Redirect if no team is found
            messages.error(request, 'You do not have any Team Page.')  # Escaped single quote
            return redirect('player-dashboard')


class UserJoinedTeamInfo(LoginRequiredMixin, View):
    template_name = 'PlayerDashboardTeams.html'  # Your template to display the team info

    def get(self, request, *args, **kwargs):
        user = request.user
        language_from_url = request.GET.get('Language', None)
        
        # Handle language selection from URL or session
        if language_from_url:
            request.session['language'] = language_from_url
        else:
            language_from_url = request.session.get('language', 'en')

        # Fetch the user's team branches and their joining type
        team_branches = self.get_user_team_branches(user)

        context = {
            "current_language": language_from_url,
            "team_branches": team_branches,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
        }

        return render(request, self.template_name, context)

    def get_user_team_branches(self, user):
        """
        Fetches the team branches that the user is part of, including their joining type (Managerial, Coach, etc.)
        """
        # Only use select_related for ForeignKey fields (branch_id, user_id)
        join_branches = JoinBranch.objects.filter(user_id=user.id).select_related('branch_id', 'user_id')
        
        team_branches = []
        for join_branch in join_branches:
            team_branch = join_branch.branch_id  # Get the related TeamBranch object
            team_branches.append({
                'team_name': team_branch.team_id.team_name,
                'branch_name': team_branch.team_name,
                'joinning_type': dict(JoinBranch.JOINNING_TYPE_CHOICES).get(join_branch.joinning_type),
                'phone': team_branch.phone,
                'age_group': team_branch.age_group_id.name_en,
                'team_logo': team_branch.team_id.team_logo.url if team_branch.team_id.team_logo else None,
            })
        
        return team_branches