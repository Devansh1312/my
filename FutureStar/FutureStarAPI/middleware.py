from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from FutureStar_App.models import User
import jwt

class MiddlewareToken(MiddlewareMixin):

    def process_request(self, request, *args, **kwargs):
        # Updated bypass_paths
        bypass_paths = (
                "/api/logout/",                        # Player Logout API
                "/api/change-password/",               # For logged-in users
                "/api/edit-profile/",                  # URL for CreateProfile API
                "/api/posts/",                         # User Post API
                "/api/posts/create/",                  # Create Post API
                "/api/posts/details/",                 # Post details API
                "/api/comments/create/",               # Create Comment API
                "/api/posts/delete/",                  # Delete Post API
                "/api/fields/",                        # Field API
                "/api/tournament/",                    # Tournament API
                "/api/team/",                          # Team API
                "/api/user/update-current-type/",      # Update Current Type API
                "/api/user_account_delete_reasons/list/", # Account Deletion Reasons List API
                "/api/delete_account/",                # Delete Account API
                "/api/update-profile-img/",            # Update Profile Image API
                "/api/stats/player_stats/",            # Player Stats API
                "/api/follow_unfollow/",               # Follow/Unfollow API
                "/api/followers/",                     # List Followers API
                "/api/following/",                     # List Following API
                "/api/posts/like/",                    # Like Post API
                "/api/posts/all/",                     # All Posts List API
                "/api/posts/edit/",                    # Edit Post API
                "/api/posts/media_delete/",            # Delete Post Media API
                "/api/comments/",                      # Comments API (paginated)
                "/api/media/album_detail/",            # Album Details API
                "/api/media/album_create/",            # Create Album API
                "/api/media/all_albums/",              # All Albums API
                "/api/media/all_photos/",              # All Photos in Gallery API
                "/api/media/all_videos/",              # All Videos in Gallery API
                "/api/media/create/",                  # Create Gallery API
                "/api/media/recent/",                  # Latest Gallery API
                "/api/media/album_delete/",            # Delete Album API
                "/api/media/delete/",                  # Delete Gallery Item API
                "/api/events/",                        # Events List API
                "/api/events/create/",                 # Create Event API
                "/api/events/types/",                  # Event Types API
                "/api/events/update/",                 # Update Event API
                "/api/events/booking/",                # Event Booking Detail API
                "/api/events/booking/create/",         # Event Booking Create API
                "/api/events/detail/",                 # Event Detail API
                "/api/events/like/",                   # Event Like API
                "/api/events/comments/",               # Event Comments (paginated)
                "/api/events/comments/create/",        # Create Event Comment API
                "/api/sponsor/",                       # Sponsor API
                "/api/sponsor/detail/",                # Sponsor Detail API
                "/api/reports/",                       # Reports List API
                "/api/reports/create/",                # Create Post Report API
                "/api/fields/list/",                   # List Fields API
                "/api/genders/",                       # User Gender List API
                "/api/age_groups/",                   # Age Groups List API
                "/api/general/settings/",              # General Settings API
                "/api/faq/",                           # FAQ API
                "/api/role/",                          # User Roles API
                "/api/locations/",                     # Locations API
                "/api/playing_positions/",             # Playing Positions List API
                "/api/injury_types/",                  # Injury Types List API
                "/api/profile/create/",                # Create Profile API
                "/api/dashboard/",                     # Dashboard API
                "/api/playing_foot/",                  # Playing Foot API
                "/api/search/",                                                # Search API
                "/api/mark-all-notifications-read/",  # Mark All Notifications as Read API
                "/api/clear-notification/",           # Clear Notification API
                "/api/notification_list/",            # Notification List API
                "/api/friendlygames/create/",               # Create Friendly Game API
                "/api/friendlygames/requested_referee/list/", # Official List API
                "/api/friendlygames/edit_detail/",          # Edit Friendly Game Detail API
                "/api/friendlygames/update/",               # Update Friendly Game API
                "/api/friendlygames/team_list_of_manager/", # Manager's Team List API
                "/api/friendlygames/delete/",               # Delete Friendly Game API
                "/api/friendlygames/detail/",               # Friendly Game Detail API
                "/api/friendly-game/list/",                 # List of Friendly Games API for Join
                "/api/friendly-game/branch_list/",          # Team Branch List API
                "/api/friendlygames/teamplayers/",          # Team Players API
                "/api/friendlygames/teamplayers/add/",      # Add Team Player API
                "/api/friendlygames/teamplayers/jersey_no/",# Player Jersey Number API
                "/api/friendlygames/teamplayers/delete/",   # Delete Team Player API
                "/api/friendlygames/lineup/",               # Friendly Game Lineup API
                "/api/friendlygames/lineup/player_substitute/", # Player Substitution API
                "/api/friendlygames/lineup/swap_position/", # Swap Player Position API
                "/api/friendlygames/lineup/fetch_position/", # Fetch Player Position API
                "/api/friendlygames/lineup/update/",        # Update Friendly Game Lineup API
                "/api/friendlygames/lineup/reset/",         # Reset Friendly Game Lineup API
                "/api/friendlygames/lineup/player_confirmation/status/", # Player Confirmation Status API
                "/api/friendlygames/lineup/player_confirmation/status_change/", # Change Player Confirmation Status API
                "/api/friendlygames/game_stats/lineup/",    # Lineup Game Stats API
                "/api/friendlygames/game_stats/player_stats/", # Player Game Stats API
                "/api/friendlygames/game_stats/timeline/",  # Player Game Stats Timeline API
                "/api/friendlygames/game_officials/type/",  # Game Official Types API
                "/api/friendlygames/game_officials/",      # Game Officials API
                "/api/friendlygames/game_officials/add/",   # Add Game Official API
                "/api/friendlygames/game_officials/remove/", # Remove Game Official API
                "/api/friendlygames/game_officials/search/", # Search Game Officials API
                "/api/friendlygames/game/linup/details/",  # Friendly Game Lineup Details API
                "/api/friendlygames/h2h/completed/",        # Completed Friendly Games API
                "/api/friendlygames/game_detail_stats/",    # Friendly Game Stats API
                "/api/friendlygames/update_result/",        # Update Friendly Game Result API
                "/api/friendlygames/team_uniform/create/",  # Create Team Uniform API
                "/api/friendlygames/team_uniform/",         # Fetch Team Uniform API
                "/api/friendlygames/uniform_fetch/",        # Fetch Friendly Game Uniform API
                "/api/teamplayers/",                        # Team Players API
                "/api/teamplayers/Add/",                    # Add Team Player API
                "/api/teamplayers/jersey_no/",              # Add Player Jersey API
                "/api/teamplayers/delete/",                 # Delete Team Player API
                "/api/lineup/update/",                     # Update Lineup API
                "/api/lineup/reset/",                      # Reset Lineup API
                "/api/lineup/",                            # Get Lineup API
                "/api/lineup/player_confirmation/status/", # Player Confirmation Status API
                "/api/lineup/player_confirmation/status_change/", # Change Player Confirmation Status API
                "/api/lineup/player_substitute/",          # Player Substitution API
                "/api/lineup/swap_position/",              # Swap Player Position API
                "/api/lineup/fetch_position/",             # Fetch Player Position API
                "/api/game_stats/lineup/",                 # Game Stats Lineup API
                "/api/game_stats/player_stats/",           # Player Game Stats API
                "/api/game_stats/timeline/",               # Team Game Stats Timeline API
                "/api/game_officials_type/",               # Game Official Types API
                "/api/game-officials/",                    # Game Officials API
                "/api/game-officials/add/",                # Add Game Official API
                "/api/game-officials/remove/",             # Remove Game Official API
                "/api/game-officials/search/",             # Search Game Officials API
                "/api/top_player_stats/",                  # Top Player Stats API
                "/api/team/",                             # Team API
                "/api/team/uniform_delete/",              # Delete Team Uniform API
                "/api/team_branch/",                      # Team Branch API
                "/api/team_branch/create/",               # Create Team Branch API
                "/api/team_branch/edit/",                 # Edit Team Branch API
                "/api/team_branch/delete/",               # Delete Team Branch API
                "/api/staff-management/",                 # Staff Management API
                "/api/search_users/",                     # User Search API
                "/api/team_total_stats/",                 # Team Total Stats API
                "/api/tournament/",                        # Tournament API
                "/api/tournament/my_tournament/",          # My Tournaments API
                "/api/tournament/create/",                 # Create Tournament API
                "/api/tournament/game/detail/",            # Game Detail API
                "/api/tournament/team_request/",           # Team Joining Request API
                "/api/tournament/team_reject/",            # Team Reject Request API
                "/api/tournament/team_accept/",            # Team Request Approved API
                "/api/tournament/detail/",                 # Tournament Detail API
                "/api/tournament/team/",                   # Tournament Group Team List API
                "/api/tournament/games/create/",           # Create Tournament Game API
                "/api/tournament/games/",                  # Tournament Games List API
                "/api/tournament/games/update/",           # Update Tournament Game API
                "/api/games/team_uniform/",                # Team Uniform Color API
                "/api/games/refree/fetch_team_uniform/",   # Fetch Team Uniform Color API
                "/api/games/uniform_fetch/",               # Game Uniform Color Fetch API
                "/api/games/refree/confirm_team_uniform/", # Confirm Team Uniform API
                "/api/tournament/game/linup/details/",    # Tournament Game Lineup Details API
                "/api/tournament/team_game_h2h/",          # Tournament Team H2H API
                "/api/tournament/games/options/",          # Tournament Game Options API
                "/api/group_table/",                       # Group Table API
                "/api/group_table/team/create/",           # Create Tournament Group Team API
                "/api/group_table/team/",                  # Tournament Group Team API
                "/api/search-team-branches/",              # Search Team Branches API
                "/api/tournaments/like/",                  # Tournament Like API
                "/api/tournaments/comments/",              # Tournament Comments API
                "/api/tournaments/comments/create/",       # Tournament Comment Create API
                "/api/upcoming/games/",                    # Upcoming Games API
                "/api/my_games/",                          # Fetch My Games API
                "/api/all_games/",                         # Fetch All Games API
                "/api/tournament/game_detail_stats/",      # Tournament Game Detail Stats API
                "/api/update_extra_time/",                 # Update Extra Time API
                "/api/training/create/",                  # Create Training API
                "/api/training/update/",                  # Update Training API
                "/api/training/delete/",                  # Delete Training API
                "/api/open_trainings/",                   # Open Trainings List API
                "/api/training/detail/",                  # Training Detail API
                "/api/training/like/",                    # Training Like API
                "/api/training/comments/",                # Training Comments API
                "/api/training/comments_create/",         # Create Training Comment API
                "/api/training/joined/",                  # Joined Training API
                "/api/training/feedback/",                # Training Feedback API
                "/api/training/mytraining/",              # My Trainings API
                "/api/training/jointarining/",            # My Joined Trainings API
            )

        # If the request path is in bypass_paths, check the token
        if any(request.path.startswith(path) for path in bypass_paths):
            # Retrieve the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'status': 2,
                    'message': 'Authorization header is missing or invalid'
                }, status=200)

            # Extract the token
            token = auth_header.split(' ')[1]

            try:
                # Decode the JWT token using the SECRET_KEY
                payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])

                # Get the user associated with the token
                user = User.objects.get(id=payload['user_id'])

                # Attach the user to the request object for use in the views
                request.user = user

            except jwt.ExpiredSignatureError:
                return JsonResponse({
                    'status': 2,
                    'message': 'Token has expired'
                }, status=200)
            except jwt.InvalidTokenError:
                return JsonResponse({
                    'status': 2,
                    'message': 'Invalid token'
                }, status=200)
            except User.DoesNotExist:
                return JsonResponse({
                    'status': 2,
                    'message': 'User does not exist'
                }, status=200)
            except Exception as e:
                # Catch any other unexpected errors
                print(f"Unknown Error: {e}")
                return JsonResponse({
                    'status': 2,
                    'message': 'Server error'
                }, status=200)

        return None  # Continue processing the request if the path is not in bypass_paths
