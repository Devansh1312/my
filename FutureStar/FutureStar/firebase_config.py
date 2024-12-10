import firebase_admin
from firebase_admin import credentials, messaging
import logging

# Initialize Firebase Admin SDK with your credentials
cred = credentials.Certificate("goalactico-7009d-firebase-adminsdk-mx0go-c9abd8706f.json")
firebase_app = firebase_admin.initialize_app(cred)

# Constants for device types
ANDROID = 1
IOS = 2

def send_push_notification(device_token, title, body, device_type, data=None):
    """
    Sends a push notification to the specified device using Firebase Cloud Messaging (FCM).
    """
    try:
        # Prepare custom data for Android
        if device_type in [1, "1"]:
            data = data or {}
            data.update({
                "title": str(title) if title else "",
                "body": str(body) if body else "",
            })
            print(data)

        # Create the notification message
        android_config = (
            messaging.AndroidConfig(
                priority="high",
                data={str(k): str(v) for k, v in data.items()},  # Ensure all keys and values are strings
            )
            if device_type in [1, "1"]
            else None
        )

        ios_config = (
            messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert={
                            "title": title,
                            "body": body,
                        },
                        content_available=True,
                    ),
                    custom_data={str(k): str(v) for k, v in (data or {}).items()},  # Ensure all keys and values are strings
                )
            )
            if device_type in [2, "2"]
            else None
        )

        message = messaging.Message(
            token=device_token,
            android=android_config,
            apns=ios_config,
        )

        # Send the notification
        response = messaging.send(message)

        # Log and return the response
        logging.info(f"Firebase response: {response}")
        print(f"Notification sent successfully: {response}")
        return response

    except Exception as e:
        logging.error(f"Error sending push notification: {str(e)}", exc_info=True)
        raise
