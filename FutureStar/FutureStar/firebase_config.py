import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK with your credentials
cred = credentials.Certificate("goalactico-7009d-firebase-adminsdk-mx0go-c9abd8706f.json")
firebase_app=firebase_admin.initialize_app(cred)

print("Firebase Initialized: ", firebase_app)


def send_push_notification(device_token, title, body, device_type):
    """
    Sends a push notification to the specified device using Firebase Cloud Messaging (FCM).
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_token,
            android=messaging.AndroidConfig(priority="high") if device_type == 1 else None,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(content_available=True),
                ),
            ) if device_type == 2 else None,
        )
        # Sending the notification
        response = messaging.send(message)
        
        # Log the response from Firebase
        print(f"Firebase response: {response}")
        return response  # Optionally, you can return the response or raise an exception for failed notifications

    except Exception as e:
        # Log the error if there is one
        print(f"Error sending message: {str(e)}")
        raise  # Re-raise the exception to handle it in views.py
