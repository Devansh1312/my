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
    age_group_name = serializers.SerializerMethodField()

    


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
            'age_group_name', 
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
            'team_id',
            
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
    def get_age_group_name(self, obj):
        return obj.age_group.name_en if obj.age_group else None


    def create(self, validated_data):
        # Automatically associate the tournament with the currently logged-in user
    
        number_of_group = validated_data.pop('number_of_group', 1)  # Get number of groups, default to 1

        # team_id = int('created_by_id')
        # try:
        #     team_id = int(validated_data.get('created_by_id'))
        # except (TypeError, ValueError):
        #     raise serializers.ValidationError({"created_by_id": "Team ID must be a valid integer."})

        # if not team_id:
        #     raise serializers.ValidationError({"created_by_id": "Team ID is required to create a tournament."})

        # if not team_id:
        #     raise serializers.ValidationError({"created_by_id": "Team ID is required to create a tournament."})

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
    
    def update(self, instance, validated_data):
        # Get the updated number of groups
        updated_number_of_groups = validated_data.get('number_of_group', instance.number_of_group)

        # Calculate the difference in the number of groups
        current_number_of_groups = instance.number_of_group
        group_difference = updated_number_of_groups - current_number_of_groups

        if group_difference > 0:
            # If increased, create the new groups
            existing_groups = GroupTable.objects.filter(tournament_id=instance).count()
            for i in range(existing_groups, existing_groups + group_difference):
                group_name = f"Group-{chr(65 + i)}"
                GroupTable.objects.create(tournament_id=instance, group_name=group_name)

        elif group_difference < 0:
            # If decreased, delete groups from the last
            groups_to_delete = list(GroupTable.objects.filter(tournament_id=instance).order_by('-id')[:abs(group_difference)])
            for group in groups_to_delete:
                group.delete()

        # Update the tournament instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class GroupTableSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField() 
    class Meta:
        model = GroupTable
        fields = ['id','name']
        
    def get_name(self,obj):
        return obj.group_name if obj.group_name else None

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
    # tournament_banner = serializers.SerializerMethodField()


   
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
    
    # def get_tournament_banner(self,obj):
    #     if obj.tournament_id:
    #         return obj.tournament_id.tournament_banner.url
    #     return None
    


class TeamUniformColorSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    tournament_id = serializers.IntegerField()
    team_id = serializers.IntegerField()  # Can be either team_a or team_b
    primary_color_player = serializers.CharField(max_length=255, required=True)
    secondary_color_player = serializers.CharField(max_length=255, required=True)
    third_color_player = serializers.CharField(max_length=255, required=True)
    primary_color_goalkeeper = serializers.CharField(max_length=255, required=True)
    secondary_color_goalkeeper = serializers.CharField(max_length=255, required=True)
    third_color_goalkeeper = serializers.CharField(max_length=255, required=True)

    def validate(self, data):
        game_id = data.get('game_id')
        tournament_id = data.get('tournament_id')
        team_id = data.get('team_id')

        try:
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            raise serializers.ValidationError("Invalid game or tournament specified.")
        
        if team_id not in [game.team_a.id, game.team_b.id]:
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
                  'game_field_name', 'game_date', 'team_a_logo', 'team_b_logo'
                ]

    def get_team_a_logo(self, obj):
        # Access the logo for team A through select_related to avoid extra queries
        if obj.team_a and obj.team_a.team_id:
            team_a_logo = obj.team_a.team_id.team_logo
            return f"/media/{team_a_logo}" if team_a_logo else None
        return None

    def get_team_b_logo(self, obj):
        # Access the logo for team B through select_related to avoid extra queries
        if obj.team_b and obj.team_b.team_id:
            team_b_logo = obj.team_b.team_id.team_logo
            return f"/media/{team_b_logo}" if team_b_logo else None
        return None

    def get_team_a_name(self, obj):
        return obj.team_a.team_name if obj.team_a else None

    def get_team_b_name(self, obj):
        return obj.team_b.team_name if obj.team_b else None

    def get_game_field_name(self, obj):
        return obj.game_field_id.field_name if obj.game_field_id else None
    

class TournamentGameSerializer(serializers.ModelSerializer):
    tournament_name = serializers.SerializerMethodField()
    group_id_name = serializers.SerializerMethodField()
    team_a_name = serializers.SerializerMethodField()
    team_b_name = serializers.SerializerMethodField()
    team_a_logo = serializers.SerializerMethodField()
    team_b_logo = serializers.SerializerMethodField()
    game_field_id_name = serializers.SerializerMethodField()

    class Meta:
        model = TournamentGames
        fields = [
            'id','tournament_id', 'game_number', 'game_date', 'game_start_time', 'game_end_time',
            'team_a_goal', 'team_b_goal', 'finish', 'winner_id', 'loser_id', 'is_draw',
            'is_confirm', 'extra_time', 'tournament_name','group_id', 'group_id_name',
            'team_a_name', 'team_a_logo', 'team_b_name', 'team_b_logo',
            'game_field_id_name'
        ]
   
    def get_tournament_name(self, obj):
        """
        Get the name of the tournament associated with the game.
        """
        return obj.tournament_id.tournament_name if obj.tournament_id else None

    def get_group_id_name(self, obj):
        """
        Get the name of the group associated with the game.
        """
        return obj.group_id.group_name if obj.group_id else None

    def get_team_a_name(self, obj):
        """
        Get the name of Team A.
        """
        return obj.team_a.team_name if obj.team_a else None

    def get_team_b_name(self, obj):
        """
        Get the name of Team B.
        """
        return obj.team_b.team_name if obj.team_b else None

    def get_team_a_logo(self, obj):
        """
        Get the logo of Team A.
        """
        if obj.team_a and hasattr(obj.team_a, 'team_id'):
            team_a_logo = obj.team_a.team_id.team_logo
            return f"/media/{team_a_logo}" if team_a_logo else None
        return None

    def get_team_b_logo(self, obj):
        """
        Get the logo of Team B.
        """
        if obj.team_b and hasattr(obj.team_b, 'team_id'):
            team_b_logo = obj.team_b.team_id.team_logo
            return f"/media/{team_b_logo}" if team_b_logo else None
        return None

    def get_game_field_id_name(self, obj):
        """
        Get the name of the game field associated with the game.
        """
        return obj.game_field_id.field_name if obj.game_field_id else None


class DetailedTournamentGroupTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentGroupTeam
        fields = [
            'id',
            'group_id',
            'team_branch_id',
            'tournament_id',
            'status',
            'created_at',
            'updated_at',
        ]

    def to_representation(self, instance):
        # Get the base representation from the serializer
        data = super().to_representation(instance)
        
        # Access related fields
        data.update({
            'group_id_name': instance.group_id.group_name if instance.group_id else None,
            'team_branch_name': instance.team_branch_id.team_name if instance.team_branch_id else None,
            'team_branch_logo': instance.team_branch_id.team_id.team_logo.url if instance.team_branch_id and instance.team_branch_id.team_id.team_logo else None,
            'tournament_id_name': instance.tournament_id.tournament_name if instance.tournament_id else None,
            'country_name': instance.team_branch_id.country_name if instance.team_branch_id and hasattr(instance.team_branch_id, 'country_name') else None,
        })
        return data