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
    Handles both Android and iOS devices. Skips sending if device type or device token is invalid.
    """
    try:
        # Validate device type
        if device_type not in [1, "1", 2, "2"]:
            logging.warning(f"Invalid device type: {device_type}. Skipping notification.")
            return

        # Validate device token
        if not isinstance(device_token, str) or not device_token.strip():
            logging.warning(f"Invalid device token: {device_token}. Skipping notification.")
            return

        # Prepare custom data for Android
        if device_type in [1, "1"]:
            data = data or {}
            data.update({
                "title": str(title) if title else "",
                "body": str(body) if body else "",
            })

        # Android configuration (optional, only used for Android devices)
        android_config = (
            messaging.AndroidConfig(
                priority="high",
                data={str(k): str(v) for k, v in data.items()},  # Ensure all keys and values are strings
            )
            if device_type in [1, "1"]
            else None
        )

        # iOS configuration (only used for iOS devices)
        ios_config = (
            messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,  # Set the title for the notification
                            body=body     # Set the body for the notification
                        ),
                        content_available=True,
                    ),
                    custom_data={str(k): str(v) for k, v in (data or {}).items()},  # Ensure all keys and values are strings
                )
            )
            if device_type in [2, "2"]
            else None
        )

        # Creating the message with either Android or iOS configuration
        message = messaging.Message(
            token=device_token,
            android=android_config,
            apns=ios_config,
        )

        # Send the notification
        response = messaging.send(message)

        # Log and return the response
        logging.info(f"Firebase response: {response}")
        return response

    except Exception as e:
        logging.error(f"Error sending push notification: {str(e)}", exc_info=True)
        raise