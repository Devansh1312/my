import mimetypes
from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions



class TournamentCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()

    class Meta:
        model = Tournament_comment
        fields = ['id', 'created_by_id', 'creator_type', 'tournament', 'parent', 'comment', 'date_created', 'replies', 'entity']

    def get_replies(self, obj):
        # Only fetch replies (children) where parent is the current comment (obj)
        replies = Tournament_comment.objects.filter(parent=obj).order_by('-date_created')
        return TournamentCommentSerializer(replies, many=True, context=self.context).data


    def get_entity(self, obj):
        # Get entity details based on creator_type
        if obj.creator_type == Tournament_comment.TEAM_TYPE:
            team = Team.objects.get(id=obj.created_by_id)
            return {
                'created_by_id': team.id,
                'name': team.team_name,
                'profile_image': team.team_logo.url if team.team_logo else None,
                'creator_type': 1
            }
        elif obj.creator_type == Tournament_comment.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=obj.created_by_id)
            return {
                'created_by_id': group.id,
                'name': group.group_name,
                'profile_image': group.group_logo.url if group.group_logo else None,
                'creator_type': 2
            }
        else:  # USER_TYPE
            user = User.objects.get(id=obj.created_by_id)
            return {
                'created_by_id': user.id,
                'username': user.username,
                'profile_image': user.profile_picture.url if user.profile_picture else None,
                'creator_type': 3
            }
        return None


class TournamentSerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField()  # To show city name
    country_name = serializers.SerializerMethodField()  # To show country name
    tournament_fields_name = serializers.SerializerMethodField()  # To show field name
    comments = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    logo=serializers.SerializerMethodField()
    tournament_banner=serializers.SerializerMethodField()

    


    class Meta:
        model = Tournament
        fields = [
            'id',
            'tournament_name',
            'tournament_starting_date',
            'tournament_final_date',
            'number_of_team',
            'number_of_group',
            'age_group',
            'country',
            'country_name',
            'city',
            'city_name',
            'tournament_fields',
            'tournament_fields_name',
            'logo',
            'tournament_banner',
            'tournament_joining_cost',
            'is_like',
            'like_count',
            'comments',
            
        ]
    
    def get_like_count(self, obj):
        return TournamentLike.objects.filter(tournament=obj).count()


    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Tournament_comment.objects.filter(tournament=obj, parent=None).count()
    
    def get_is_like(self, obj):
        request = self.context.get('request')
        if request:
            # Retrieve creator_type and created_by_id from request data or query parameters
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')

            # Use default values if neither request data nor query parameters provide valid values
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else TournamentLike.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id

            # Check if a like exists for the given tournament, creator_type, and created_by_id
            if TournamentLike.objects.filter(
                tournament=obj,
                created_by_id=created_by_id,
                creator_type=creator_type
            ).exists():
                return True

        return False

    def get_country_name(self, obj):
        return obj.country.name if obj.country else None  # Return country name or None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None  # Return city name or None
    
    def get_tournament_fields_name(self, obj):
        return obj.tournament_fields.field_name if obj.tournament_fields else None  # Return field name or None
    def get_logo(self, obj):
        # Return the relative path of the logo
        return obj.logo.url if obj.logo else None

    def get_tournament_banner(self, obj):
        # Return the relative path of the tournament banner
        return obj.tournament_banner.url if obj.tournament_banner else None


    def create(self, validated_data):
        # Automatically associate the tournament with the currently logged-in user
    
        number_of_group = validated_data.pop('number_of_group', 1)  # Get number of groups, default to 1

        # Dynamically create group names based on the number of groups
        if number_of_group < 1:
            raise serializers.ValidationError("Number of groups must be at least 1.")

        # Generate group names dynamically like 'Group-A', 'Group-B', 'Group-C', ...
        group_names = [f"Group-{chr(65 + i)}" for i in range(number_of_group)]

        # Create the tournament instance
        tournament = Tournament.objects.create(number_of_group=number_of_group, **validated_data)

        # Create corresponding groups in GroupTable
        for group_name in group_names:
            GroupTable.objects.create(tournament_id=tournament, group_name=group_name)

        return tournament



class GroupTableSerializer(serializers.ModelSerializer):
    tournament_id_name = serializers.SerializerMethodField() 
    class Meta:
        model = GroupTable
        fields = ['id','tournament_id','tournament_id_name','group_name','created_at','updated_at']

    def get_tournament_id_name(self, obj):
        return obj.tournament_id.tournament_name if obj.tournament_id else None

class TournamentGroupTeamSerializer(serializers.ModelSerializer):
    group_id_name = serializers.SerializerMethodField()
    team_branch_name = serializers.SerializerMethodField()
    tournament_id_name = serializers.SerializerMethodField()
    team_branch_logo= serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()

    
    class Meta:
        model = TournamentGroupTeam
        fields = ['id','group_id','group_id_name','team_branch_id','team_branch_name','team_branch_logo','tournament_id','tournament_id_name','country_name', 'status','created_at','updated_at']

    def get_country_name(self, obj):
        try:
            # Safely access nested relationships
            if obj.team_branch_id and obj.team_branch_id.team_id and obj.team_branch_id.team_id.country_id:
                return obj.team_branch_id.team_id.country_id.name
        except AttributeError:
            pass
        return None


    def get_group_id_name(self, obj):
        return obj.group_id.group_name if obj.group_id else None
    
    def get_team_branch_name(self, obj):
        return obj.team_branch_id.team_name if obj.team_branch_id else None
    
    def get_tournament_id_name(self, obj):
        return obj.tournament_id.tournament_name if obj.tournament_id else None
    
    def get_team_branch_logo(self, obj):
        if obj.team_branch_id and obj.team_branch_id.team_id and obj.team_branch_id.team_id.team_logo:
             return obj.team_branch_id.team_id.team_logo.url
        return None
    

class TournamentGamesSerializer(serializers.ModelSerializer):
    group_id_name = serializers.SerializerMethodField()
    game_field_id_name = serializers.SerializerMethodField()
    tournament_name= serializers.SerializerMethodField()


   
    class Meta:
        model = TournamentGames
        fields = [
            'id', 'tournament_id','tournament_name','game_number', 'game_date', 'game_start_time', 'game_end_time',
            'group_id', 'group_id_name', 'team_a','team_a_goal','team_b','team_b_goal', 
            'game_field_id', 'game_field_id_name', 'finish','winner_id','loser_id','is_draw' ,'created_at', 'updated_at'
        ]

    def get_group_id_name(self, obj):
        return obj.group_id.group_name if obj.group_id else None

    def get_game_field_id_name(self, obj):
        return obj.game_field_id.field_name if obj.game_field_id else None

    def get_tournament_name(self, obj):
        # Check if group_id is set and retrieve its related tournament_id
        if obj.tournament_id:
            return obj.tournament_id.tournament_name
        return None 
    


class TeamUniformColorSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    tournament_id = serializers.IntegerField()
    team_id = serializers.CharField()  # Can be either team_a or team_b
    primary_color_player = serializers.CharField(max_length=255, required=True)
    secondary_color_player = serializers.CharField(max_length=255, required=True)
    primary_color_goalkeeper = serializers.CharField(max_length=255, required=True)
    secondary_color_goalkeeper = serializers.CharField(max_length=255, required=True)

    def validate(self, data):
        game_id = data.get('game_id')
        tournament_id = data.get('tournament_id')
        team_id = data.get('team_id')

        try:
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            raise serializers.ValidationError("Invalid game or tournament specified.")
        
        if team_id not in [game.team_a, game.team_b]:
            raise serializers.ValidationError("The specified team_id does not match any team in this game.")
        
        return data
    

class TournamentGamesHead2HeadSerializer(serializers.ModelSerializer):
    team_a_logo = serializers.SerializerMethodField()
    team_b_logo = serializers.SerializerMethodField()
    team_a_name = serializers.SerializerMethodField()
    team_b_name = serializers.SerializerMethodField()
    game_field_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TournamentGames
        fields = ['id', 'team_a_name', 'team_b_name', 'team_a_goal', 'team_b_goal', 
                  'game_field_name', 'game_date', 'team_a_logo', 'team_b_logo']

    def get_team_a_logo(self, obj):
        # Retrieve the logo for team A
        team_a_branch = TeamBranch.objects.filter(id=obj.team_a).first()
        if team_a_branch and team_a_branch.team_id:
            team_a_logo = Team.objects.filter(id=team_a_branch.team_id.id).values_list('team_logo', flat=True).first()
            return f"/media/{team_a_logo}" if team_a_logo else None
        return None

    def get_team_b_logo(self, obj):
        # Retrieve the logo for team B
        team_b_branch = TeamBranch.objects.filter(id=obj.team_b).first()
        if team_b_branch and team_b_branch.team_id:
            team_b_logo = Team.objects.filter(id=team_b_branch.team_id.id).values_list('team_logo', flat=True).first()
            return f"/media/{team_b_logo}" if team_b_logo else None
        return None

    def get_team_a_name(self, obj):
        # Retrieve the team name for team A
        team_a_branch = TeamBranch.objects.filter(id=obj.team_a).first()
        return team_a_branch.team_name if team_a_branch else None

    def get_team_b_name(self, obj):
        # Retrieve the team name for team B
        team_b_branch = TeamBranch.objects.filter(id=obj.team_b).first()
        return team_b_branch.team_name if team_b_branch else None

    def get_game_field_name(self, obj):
        # Retrieve the field name where the game is played
        game_field = Field.objects.filter(id=obj.game_field_id.id).first()
        return game_field.field_name if game_field else None