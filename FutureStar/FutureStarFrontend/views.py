from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarGameSystem.models import *
from FutureStarFriendlyGame.models import *
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import activate
from django.contrib.auth import authenticate, login
import random
from django.db.models import Q,Sum,When,Case,F



##############################################   HomePage   ########################################################

class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        cmsfeatures = cms_home_dynamic_field.objects.all() or None
        cms_home_dynamic_achivements = cms_home_dynamic_achivements_field.objects.all() or None

        try:
            cmsdata = cms_pages.objects.get(id=1)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        current_language = request.session.get('language', 'en')

        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
            "team_members": team_members,
            "cmsdata": cmsdata,
            "current_language":current_language,
            "cmsfeatures":cmsfeatures,
            "cms_home_dynamic_achivements":cms_home_dynamic_achivements,


        }
        return render(request, "home.html", context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('index')



##############################################   DiscoverPage   ########################################################

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        dynamic = cms_dicovery_dynamic_image.objects.all()
        whyus = cms_dicovery_dynamic_view.objects.all()
        try:
            cmsdata = cms_pages.objects.get(id=2)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "dynamic":dynamic,
            "whyus":whyus
        }
        return render(request, "discover.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('discover')  



##############################################   SuccessStoriesPage   ########################################################

class SuccessStoriesPage(View):
    
    def get(self, request, *args, **kwargs):
        tryout_clubs = Tryout_Club.objects.all()
        current_language = request.session.get('language', 'en')

        try:
            cmsdata = cms_pages.objects.get(id=3)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "tryout_clubs": tryout_clubs,
            "cmsdata":cmsdata,                        
            "current_language": current_language,

        }
        return render(request, "success-stories.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('success-stories')
    

##############################################   NewsPage   ########################################################

class NewsPage(View):
    
    def get(self, request, *args, **kwargs):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')
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
            "current_language": current_language,
            "cmsdata" : cmsdata,
        }
        return render(request, "news.html", context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('news')
    

##############################################   NewsDetailPage   ########################################################

class NewsDetailPage(View):
    def get(self, request, pk):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')

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
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "news-details.html", context)
    
    def post(self, request, pk):
        # Handle language change
        selected_language = request.POST.get('language', 'en')

        # Store the selected language in the session
        request.session['language'] = selected_language

        # Redirect to the same news detail page with the correct pk
        return redirect('news-detail', pk=pk)



##############################################   AdvertisePage   ########################################################

class AdvertisePage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        dynamic_field = cms_advertise_section_2_dynamic_field.objects.all()
        partnership_dynamic_field = cms_advertise_Partnership_dynamic_field.objects.all()
        ads_dynamic_field = cms_advertise_ads_dynamic_field.objects.all()
        premium_dynamic_field = cms_advertise_premium_dynamic_field.objects.all()

        try:
            cmsdata = cms_pages.objects.get(id=6)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "dynamic_field":dynamic_field,
            "partnership_dynamic_field":partnership_dynamic_field,
            "ads_dynamic_field":ads_dynamic_field,
            "premium_dynamic_field":premium_dynamic_field,
        }
       
        return render(request, "advertise.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('advertise')

##############################################   AboutPage   ########################################################

class AboutPage(View):
    
    def get(self, request, *args, **kwargs):
        
        marquee = Slider_Content.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        global_clients = Global_Clients.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=7)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "marquee": marquee,
            "testimonials": testimonials,
            "global_clients": global_clients,
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "team_members" : team_members,

        }
        return render(request, "about.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        return redirect('about')


##############################################   ContactPage   ########################################################

class ContactPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=8)  # Fetch the CMS data
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle case where the CMS data doesn't exist

        current_language = request.session.get('language', 'en')

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "contact.html", context)

    def post(self, request):
        # Fetch form data
        fullname = request.POST.get("fullname", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        selected_language = request.POST.get('language', 'en')
        current_language = request.session['language'] = selected_language

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
                "current_language": current_language,
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
        
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=10)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist


        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        } 
        return render(request, "privacy-policy.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('privacy-policy')
    

##############################################   TermsofServicesPage   ########################################################

class TermsofServicesPage(View):
    
    def get(self, request, *args, **kwargs):

        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')
        
        try:
            cmsdata = cms_pages.objects.get(id=9)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
            

        context = {
            "current_language": language_from_url,
            "cmsdata": cmsdata,
        } 

        return render(request, "terms-of-services.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('terms-of-services')  


######################### terms-of-conditions #####################

class TermsAndConditionsPage(View):
    
    def get(self, request, *args, **kwargs):
        # Check if the 'Language' parameter is in the URL
        language_from_url = request.GET.get('Language', None)
        
        if language_from_url:
            # If 'Language' parameter is in the URL, save it to the session
            request.session['language'] = language_from_url
        else:
            # If not, fall back to session language
            language_from_url = request.session.get('language', 'en')

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
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('terms-and-conditions')


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

    from datetime import datetime

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

            # Debug: Print time_filter
            print("Time filter:", time_filter)

            # 1. Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],  # IDs representing referee roles
                **time_filter
            ).values_list('game_id', flat=True)

            # Debug: Print results for officiated tournament games
            print("Tournament Games Officiated:", tournament_games_officiated)

            # 2. Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

            # Debug: Print results for officiated friendly games
            print("Friendly Games Officiated:", friendly_games_officiated)

            # 3. Calculate total games officiated
            total_games_officiated = len(tournament_games_officiated) + len(friendly_games_officiated)

            # Debug: Print total games officiated
            print("Total Games Officiated:", total_games_officiated)

            # 4. Cards stats (yellow and red cards)
            cards_stats = PlayerGameStats.objects.filter(
                game_id__in=list(tournament_games_officiated) + list(friendly_games_officiated),
                **time_filter
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )

            # Debug: Print cards stats
            print("Cards Stats:", cards_stats)

            total_yellow_cards = cards_stats['total_yellow_cards'] or 0
            total_red_cards = cards_stats['total_red_cards'] or 0

            # 5. Fetch Upcoming Games
            current_datetime = datetime.now()

            # Debug: Print current date and time
            print("Current Date and Time:", current_datetime)

            # 6. Upcoming tournament games
            upcoming_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games

            # Debug: Print upcoming tournament games
            print("Upcoming Tournament Games:", upcoming_tournament_games)

            # 7. Upcoming friendly games
            upcoming_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False
            ).order_by('game_date')[:5]  # Get the next 5 upcoming games

            # Debug: Print upcoming friendly games
            print("Upcoming Friendly Games:", upcoming_friendly_games)

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

            # Debug: Print finished tournament games
            print("Finished Tournament Games:", finished_tournament_games)

            finished_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__lt=current_datetime.date(),
                # finish=True
            ).order_by('game_date')[:5]  # Get the last 5 finished games

            # Debug: Print finished friendly games
            print("Finished Friendly Games:", finished_friendly_games)

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

            # Debug: Print sorted finished games
            print("Finished Games:", finished_games)

            # Return the stats
            return {
                "matchplayed": total_games_officiated,
                "yellow_card": total_yellow_cards,
                "red": total_red_cards,
                "upcoming_games": sorted(upcoming_games, key=lambda x: x["game_date"]),
                "finished_games": finished_games,
            }
        except Exception as e:
            # Debugging: Print exception message
            print("Error:", str(e))
            return {"status": 0, "message": "Failed to fetch referee stats.", "error": str(e)}



    def get(self, request, *args, **kwargs):
        user = request.user
        current_language = request.session.get('language', 'en')

        # Fetch user-related data
        teams, stats = self.get_user_related_data(user)
        context = {
            "current_language": current_language,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "teams": teams,
            "stats": stats,
            
        }

        return render(request, "PlayerDashboard.html", context)


    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('player-dashboard')
  






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
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=12)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
            # Uncomment these lines if needed
            # "google_client_id": settings.GOOGLE_CLIENT_ID,
            # "apple_client_id": settings.APPLE_CLIENT_ID,
            # "apple_redirect_uri": settings.APPLE_REDIRECT_URI,
            # "social_auth_state_string": settings.SOCIAL_AUTH_STATE_STRING,
        }

        return render(request, "login.html", context)

    def post(self, request, *args, **kwargs):
        # Handle language change
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        # Fetch login type
        login_type = int(request.POST.get('login_type', 1))
        username_or_phone = request.POST.get('username_or_phone')
        password = request.POST.get('password')

        # If only language is changed (no login fields are filled)
        if not username_or_phone and not password:
            messages.success(request, "Language changed successfully!")
            return redirect('login')

        # Proceed with the login process
        if login_type == 1:
            # Custom login logic for username or phone number
            user = self.authenticate_username_or_phone(username_or_phone, password)

            if user:
                if user.is_active:
                    login(request, user)
                    user.device_type = "Website"
                    user.last_login = timezone.now()
                    user.save()
                    messages.success(request, "Login successful!")
                    return redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
                else:
                    messages.error(request, "Account is inactive.")
            else:
                messages.error(request, "Invalid credentials.")

        return redirect('login')

    #     elif login_type == 2:
    #         google_token = request.POST.get('google_token')
    #         if google_token:
    #             google_user_info = self.verify_google_token(google_token)
    #             if google_user_info:
    #                 return self.handle_social_login(request, google_user_info, login_type='google')

    #         messages.error(request, "Failed to authenticate with Google.")
    #         return redirect('login')

    #     elif login_type == 3:
    #         apple_token = request.POST.get('apple_token')
    #         if apple_token:
    #             apple_user_info = self.verify_apple_token(apple_token)
    #             if apple_user_info:
    #                 return self.handle_social_login(request, apple_user_info, login_type='apple')

    #         messages.error(request, "Failed to authenticate with Apple.")
    #         return redirect('login')

    #     messages.error(request, "Invalid login type.")
    #     return redirect('login')

    # def verify_google_token(self, token):
    #     try:
    #         response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={token}')
    #         if response.status_code == 200:
    #             return response.json()
    #     except Exception as e:
    #         print(f"Error verifying Google token: {e}")
    #     return None

    # def verify_apple_token(self, token):
    #     try:
    #         apple_public_keys = requests.get('https://appleid.apple.com/auth/keys').json()
    #         key = apple_public_keys['keys'][0]
    #         decoded_token = decode(token, key, algorithms=['RS256'], audience=settings.APPLE_CLIENT_ID)
    #         return decoded_token
    #     except exceptions.InvalidTokenError as e:
    #         print(f"Error verifying Apple token: {e}")
    #     return None

    # def handle_social_login(self, request, user_info, login_type):
    #     email = user_info.get('email')
    #     if not email:
    #         messages.error(request, f"Unable to retrieve email for {login_type} login.")
    #         return redirect('login')

    #     user = User.objects.filter(email=email).first()

    #     if user:
    #         if user.is_active:
    #             login(request, user)
    #             user.device_type = "Website"
    #             user.last_login = timezone.now()
    #             user.save()
    #             messages.success(request, f"Login successful via {login_type.capitalize()}!")
    #             return redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
    #         else:
    #             messages.error(request, "Account is inactive.")
    #             return redirect('login')
    #     else:
    #         username = email.split('@')[0]
    #         user = User.objects.create_user(
    #             username=username,
    #             email=email,
    #             password=None,
    #             role_id=2,
    #             is_active=True,
    #         )
    #         login(request, user)
    #         user.device_type = "Website"
    #         user.last_login = timezone.now()
    #         user.save()
    #         messages.success(request, f"User created and login successful via {login_type.capitalize()}!")
    #         return redirect('player-dashboard')




# Generate a random 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

#################################### Register Page ##########################################
class RegisterPage(View):
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        # Fetching specific CMS data
        try:
            cmsdata = cms_pages.objects.get(id=13)
        except cms_pages.DoesNotExist:
            cmsdata = None

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "register.html", context)

    def post(self, request, *args, **kwargs):
        register_type = request.POST.get("register_type")
        
        if register_type == "1":  # Normal registration
            return self.handle_normal_registration(request)
        
        else:  # Google or Apple sign-up
            email = request.POST.get("email")  # Get email from OAuth
            return self.handle_social_signup(email, register_type)

    def handle_normal_registration(self, request):
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
        messages.success(request, f"Your OTP is {otp}")
        return redirect("verify_otp")

    def handle_social_signup(self, email, register_type):
        # Redirect to the username and phone entry page
        return redirect('social_signup', email=email, register_type=register_type)

class SocialSignupView(View):
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email')
        register_type = request.GET.get('register_type')

        context = {
            'email': email,
            'register_type': register_type,
        }
        return render(request, "social_signup.html", context)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        register_type = request.POST.get("register_type")

        # Validate username and phone number
        if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
            messages.error(request, "Username or phone number already exists.")
            return redirect("social_signup", email=email, register_type=register_type)

        # Generate OTP and save user details in OTPSave table
        otp = generate_otp()
        OTPSave.objects.create(username=username, phone=phone, email=email, OTP=otp)

        # Log the OTP for development purposes

        # Store necessary data in the session
        request.session['username'] = username
        request.session['phone'] = phone
        request.session['email'] = email

        return redirect("verify_otp")

#################################### OTP Verification #######################################
class OTPVerificationView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "otp_verification.html")

    def post(self, request, *args, **kwargs):
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
            device_type="web"
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
    

############################### google ###########################
# class GoogleLoginView(View):
#     def get(self, request):
#         # Step 1: Redirect user to Google OAuth 2.0 URL
#         google_auth_url = (
#             f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}"
#             f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=email profile"
#         )
#         return redirect(google_auth_url)

# class GoogleCallbackView(View):
#     def get(self, request):
#         # Step 2: Handle callback from Google
#         code = request.GET.get('code')
#         token_url = 'https://oauth2.googleapis.com/token'

#         # Exchange authorization code for access token
#         token_data = {
#             'code': code,
#             'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
#             'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
#             'redirect_uri': settings.GOOGLE_REDIRECT_URI,
#             'grant_type': 'authorization_code'
#         }
#         token_r = requests.post(token_url, data=token_data)
#         token_json = token_r.json()
#         access_token = token_json.get('access_token')

#         # Step 3: Retrieve user info from Google
#         userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
#         headers = {'Authorization': f'Bearer {access_token}'}
#         userinfo_r = requests.get(userinfo_url, headers=headers)
#         user_info = userinfo_r.json()

#         email = user_info.get('email')
#         print(email)
#         username = user_info.get('name')

#         # Check if user already exists
#         user= User.objects.get_or_create(
#             username=username,
#             defaults={'email': email, 'register_type': '2'}
#         )

#         return redirect('social_signup',user)  # Redirect to your desired page


########################## Apple ###########################
# class AppleLoginView(View):
#     def get(self, request):
#         # Step 1: Redirect to Apple Sign-In page
#         apple_auth_url = (
#             f"https://appleid.apple.com/auth/authorize?response_type=code&client_id={settings.SOCIAL_AUTH_APPLE_ID}"
#             f"&redirect_uri={settings.APPLE_REDIRECT_URI}&scope=email%20name"
#         )
#         return redirect(apple_auth_url)
    
# class AppleCallbackView(View):
#     def get(self, request):
#         # Step 2: Handle the callback from Apple
#         code = request.GET.get('code')
#         token_url = 'https://appleid.apple.com/auth/token'

#         # Exchange authorization code for access token
#         token_data = {
#             'code': code,
#             'client_id': settings.SOCIAL_AUTH_APPLE_ID,
#             'client_secret': settings.SOCIAL_AUTH_APPLE_SECRET,
#             'redirect_uri': settings.APPLE_REDIRECT_URI,
#             'grant_type': 'authorization_code'
#         }
#         token_r = requests.post(token_url, data=token_data)
#         token_json = token_r.json()
#         access_token = token_json.get('access_token')

#         # Step 3: Retrieve user info from Apple
#         userinfo_url = 'https://appleid.apple.com/auth/userinfo'
#         headers = {'Authorization': f'Bearer {access_token}'}
#         userinfo_r = requests.get(userinfo_url, headers=headers)
#         user_info = userinfo_r.json()

#         email = user_info.get('email')
#         username = user_info.get('name')

#         # Check if user already exists
#         user = User.objects.filter(email=email).first()  # Fetch user based on email

#         if user:
#             # If the user already exists, prompt to log in
#             messages.error(request, "This Apple ID is already registered. Please log in.")
#             return redirect("login")  # Redirect to your login view

#         # If not registered, proceed with OTP flow
#         otp = generate_otp()  # Generate OTP as per your existing logic

#         # Save user details in OTPSave table
#         OTPSave.objects.create(username=username, phone=None, email=email, OTP=otp)

#         # Log the OTP for development purposes

       ## # # Store necessary data in the session
       ## # request.session['username'] = username
       ## # request.session['email'] = email

       ## # messages.success(request, f"An OTP has been sent to your registered email: {email}")
       ## # return redirect("verify_otp")  # Redirect to the OTP verification page
       ## # Check if user already exists
#         user= User.objects.get_or_create(
#             username=username,
#             defaults={'email': email, 'register_type': '2'}
#         )

#         return redirect('social_signup',user)  # Redirect to your desired page



class UserDashboardGames(LoginRequiredMixin,View):

    def get(self, request, *args, **kwargs):
        user = request.user
        current_language = request.session.get('language', 'en')

        # Fetch user-related data
        stats = self.get_user_dashboard_games(user)
        context = {
            "current_language": current_language,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "stats": stats,
            
        }

        return render(request, "PlayerDashboardGames.html", context)


    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('player-dashboard')
    
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

            # Debugging: Print time_filter
            print("Time filter:", time_filter)

            # Check if the user is an official in any game (official types 2, 3, 4, 5)
            is_official = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5]
            ).exists() or FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5]
            ).exists()

            print("Is user an official?", is_official)

            # If the user is not an official for any game, return an appropriate message
            if not is_official:
                return {"status": 0, "message": "User is not an official for any game."}

            # Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],  # IDs representing referee roles
                **time_filter
            ).values_list('game_id', flat=True)
            print("Tournament Games Officiated:", tournament_games_officiated)

            # Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)
            print("Friendly Games Officiated:", friendly_games_officiated)

            # Fetch Upcoming Games
            current_datetime = datetime.now()
            print("Current Date and Time:", current_datetime)

            # Upcoming tournament games
            upcoming_tournament_games = TournamentGames.objects.filter(
                id__in=tournament_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False  # Ensure the game is not finished
            ).order_by('game_date')
            print("Upcoming Tournament Games:", upcoming_tournament_games)

            # Upcoming friendly games
            upcoming_friendly_games = FriendlyGame.objects.filter(
                id__in=friendly_games_officiated,
                game_date__gte=current_datetime.date(),
                finish=False  # Ensure the game is not finished
            ).order_by('game_date')
            print("Upcoming Friendly Games:", upcoming_friendly_games)

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
        print("I'm Player")
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
        current_language = request.session.get('language', 'en')

        # Fetch user-related data
        events = self.get_user_event_bookings(user)
        context = {
            "current_language": current_language,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
            "events": events,
        }

        return render(request, "PlayerDashboardEvents.html", context)

    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('player-dashboard')

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
        current_language = request.session.get('language', 'en')
        # Fetch fields created by the current user
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
        
        print(fields_data)
        context = {
            'fields': fields_data,
            "current_language": current_language,
            "cmsdata": cms_pages.objects.filter(id=14).first(),
        }
        return render(request, 'PlayerDashboardFields.html', context)
