import os, json, base64
import slack
import hug
import make_iap_request as iap
from datetime import datetime
from tzlocal import get_localzone
from flask import jsonify
import re
import base64
import requests

print("running")

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])
SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['SERVICE_ACCOUNT_KEY'])
verification_token=os.environ['VERIFICATION_TOKEN']
IAP_CLIENT_ID = os.environ['IAP_CLIENT_ID']
IAP_REQUEST_URL = os.environ['IAP_REQUEST_URL']
_LOCAL_TZ = get_localzone()

@hug.get(examples='message=hello world&channel=cloud-run')
@hug.local()
def post_to_channel(message: hug.types.text, channel: hug.types.text, hug_timer=3):
    """Post a message to a Slack Channel"""

    response = client.chat_postMessage(
        channel='#' + channel,
        text=message)
    assert response["ok"]
    assert response["message"]["text"] == message

    return {'message': message,
            'channel': channel,
            'took': float(hug_timer)}

@hug.get(examples='message=hello world&userId=U0BDT1R0W')
@hug.local()
def post_to_user_by_id(message: hug.types.text, userId: hug.types.text, hug_timer=3):
    """Post a message to a Slack User by UserId"""

    response = client.chat_postMessage(
        channel=userId,
        text=message)
    assert response["ok"]
    assert response["message"]["text"] == message

    return {'message': message,
            'user': userId,
            'took': float(hug_timer)}

@hug.post()
@hug.local()
def slash(body):
    print("starting slash")
    print(body)
    """Respond to a Slack command"""
    if body['token'] == verification_token:
        print("token ok")

        time_now = datetime.now(_LOCAL_TZ)
        time_ident = time_now.strftime('%Y%m%d%H%M%s%Z')

        payload = {
            'run_id': 'post-triggered-run-%s' % time_ident,
            'conf': json.dumps({'started_by' : body['user_name']}),
        }
        try:
            service_account_json = json.loads(SERVICE_ACCOUNT_KEY)
            x = iap.make_iap_request(IAP_REQUEST_URL, IAP_CLIENT_ID, service_account_json, method='POST', data=json.dumps(payload))
        except:
            response = {
                "response_type": "in_channel",
                "text": "Sorry, could not start the training run."
            }
            print(response)
            return {response}

        parsed_message = json.loads(x)

        if "message" in parsed_message.keys():
            print("message in key")
            print(parsed_message)
            datetime_object = datetime.now(_LOCAL_TZ)
            time_string = re.search("([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", parsed_message['message'])
            datetime_object = datetime.strptime(time_string.group(), '%Y-%m-%d %H:%M:%S')

        return {"response_type": "in_channel",
                "text": "<@{}> has started a lens model training run.  It's identifier will be *[{}]*".format(body['user_name'], datetime_object.strftime('%Y%m%d_%H%M%S'))}
