from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Dialogflow Webhook request structure (simplified for intents)
class DialogflowRequest(BaseModel):
    queryResult: dict
    originalDetectIntentRequest: Optional[dict] = None

@app.post("/webhook")
async def dialogflow_fulfillment(request: Request):
    body = await request.json()
    print("Request Body:", body)  # Log the request body to see what's coming from Dialogflow
    intent = body['queryResult']['intent']['displayName']

    if intent == 'request_permission':
        return {
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "systemIntent": {
                        "intent": "actions.intent.PERMISSION",
                        "data": {
                            "@type": "type.googleapis.com/google.actions.v2.PermissionValueSpec",
                            "optContext": "To locate you",
                            "permissions": ["DEVICE_PRECISE_LOCATION"]
                        }
                    }
                }
            }
        }

    elif intent == 'user_info':
        try:
            permission_granted = body['originalDetectIntentRequest']['payload']['inputs'][0]['arguments'][0]['boolValue']
            print("Permission Granted:", permission_granted)
        except (KeyError, IndexError):
            permission_granted = False
            print("Permission Not Granted")

        if permission_granted:
            try:
                location = body['originalDetectIntentRequest']['payload']['device']['location']
                latitude = location['coordinates']['latitude']
                longitude = location['coordinates']['longitude']
                print(f"Location: lat {latitude}, lon {longitude}")
                return {
                    "fulfillmentText": f"You are at latitude {latitude} and longitude {longitude}"
                }
            except KeyError:
                print("Location not found")
                return {
                    "fulfillmentText": "Sorry, I could not figure out where you are."
                }
        else:
            return {
                "fulfillmentText": "Permission was not granted to access your location."
            }

    return {"fulfillmentText": "Unknown intent."}
