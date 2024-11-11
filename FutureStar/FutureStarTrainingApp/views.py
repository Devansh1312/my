from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Training
from .serializers import TrainingSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from django.utils.translation import activate 
from django.core.files.storage import default_storage
from datetime import date


class CreateTrainingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en') 
        if language in ['en', 'ar']:
            activate(language)

        # Pass the full 'request' object in the context
        context = {'request': request}

        # Initialize the serializer with the context
        serializer = TrainingSerializer(data=request.data, context=context)

        if serializer.is_valid():
            # Handle image saving logic if training photo is uploaded
            if "training_photo" in request.FILES:
                image = request.FILES["training_photo"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)

                file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"

                # Save the image using the default storage
                image_path = default_storage.save(file_name, image)
                serializer.validated_data['training_photo'] = image_path

            # Save the new training instance
            training_instance = serializer.save()

            # Re-fetch the training instance with the correct context for language handling
            training_instance = Training.objects.get(id=training_instance.id)

            # Re-serialize the training instance to apply language-specific fields
            serializer = TrainingSerializer(training_instance, context={'request': request})

            # Return the successfully created training data
            return Response({
                'status': 1,
                'message': _("Training successfully created"),
                'data': serializer.data  # Use the re-serialized data with language context
            }, status=status.HTTP_201_CREATED)

        # If validation fails, return the errors
        return Response({
            'status': 0,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



#### VIEW TO RETRIEVE ALL OPEN TRAININGS FOR THE USER  ####
class OpenTrainingListView(APIView):
    def get(self, request, *args, **kwargs):
        # Get today's date
        today = date.today()

        # Query all open training sessions that have not passed
        open_trainings = Training.objects.filter(
            training_type=Training.OPEN_TRAINING,
            training_date__gte=today  # Only future or today
        )

        # Serialize the data
        serializer = TrainingSerializer(open_trainings, many=True, context={'request': request})

        return Response({
            'status': 1,
            'message': "Open trainings retrieved successfully",
            'data': serializer.data
        }, status=status.HTTP_200_OK)