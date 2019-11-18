import os, json, base64
import slack
import hug
import make_iap_request as iap
from datetime import datetime
from tzlocal import get_localzone
import re

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])
SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['SERVICE_ACCOUNT_KEY'])
verification_token=os.environ['VERIFICATION_TOKEN']
IAP_CLIENT_ID = os.environ['IAP_CLIENT_ID']
IAP_REQUEST_URL = os.environ['IAP_REQUEST_URL']
_LOCAL_TZ = get_localzone()

@hug.post()
@hug.local()
def slash(body):
    print("starting slash")
    print(body)
    """Respond to a Slack command"""
    if body['token'] == verification_token:
        print("token ok")

        validEnvironments = ['dev', 'staging', 'prod']
        time_now = datetime.now(_LOCAL_TZ)
        time_ident = time_now.strftime('%Y%m%d%H%M%s%Z')

        payload = {
            'run_id': 'post-triggered-run-%s' % time_ident,
            'conf': json.dumps({'started_by' : body['user_name']}),
        }

        if 'text' in body:
            params = body['text'].strip()
            options = params.split()
            environment = options[0]

            if (len(options) > 1):
                MODEL = options[1]
            else:
                MODEL = 'lens'

            payload['model'] = MODEL

            if (environment not in validEnvironments):
                response = {
                    "response_type": "in_channel",
                    "text": "Please specify a valid environment to run model build on [stage|prod]"
                }
                print(response)
                return response

            if environment == 'prod':
                SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['PROD_SERVICE_ACCOUNT_KEY'])
                IAP_CLIENT_ID = os.environ['PROD_IAP_CLIENT_ID']
                IAP_REQUEST_URL = os.environ['PROD_IAP_REQUEST_URL']
                PLATFORM = '`production`'
            else:
                SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['STAGE_SERVICE_ACCOUNT_KEY'])
                IAP_CLIENT_ID = os.environ['STAGE_IAP_CLIENT_ID']
                IAP_REQUEST_URL = os.environ['STAGE_IAP_REQUEST_URL']
                PLATFORM = '`staging`'

        else:
            response = {
                "response_type": "in_channel",
                "text": "Please pass some parameters i.e /buildlensmodel [environment] [modeltype]"
            }
            print(response)
            return response

        # if 'text' in body and (body['text'] == 'dev' or body['text'] == 'stage'):
        #     # Set stage airflow creds
        #     SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['STAGE_SERVICE_ACCOUNT_KEY'])
        #     IAP_CLIENT_ID = os.environ['STAGE_IAP_CLIENT_ID']
        #     IAP_REQUEST_URL = os.environ['STAGE_IAP_REQUEST_URL']
        #     PLATFORM = '`staging`'
        # elif 'text' in body and body['text'] == 'prod':
        #     # Set prod airflow creds
        #     SERVICE_ACCOUNT_KEY = base64.b64decode(os.environ['PROD_SERVICE_ACCOUNT_KEY'])
        #     IAP_CLIENT_ID = os.environ['PROD_IAP_CLIENT_ID']
        #     IAP_REQUEST_URL = os.environ['PROD_IAP_REQUEST_URL']
        #     PLATFORM = '`production`'
        # else:
        #     print(body['text'])
        #     response = {
        #         "response_type": "in_channel",
        #         "text": "Please specify which platform you want to start training on stage|prod"
        #     }
        #     print(response)
        #     return response

        print(payload)
        try:
            service_account_json = json.loads(SERVICE_ACCOUNT_KEY)
            x = iap.make_iap_request(IAP_REQUEST_URL, IAP_CLIENT_ID, service_account_json, method='POST', data=json.dumps(payload))
        except:
            response = {
                "response_type": "in_channel",
                "text": "Sorry, could not start the {} training run.".format(PLATFORM)
            }
            print(response)
            return response

        parsed_message = json.loads(x)

        if "message" in parsed_message.keys():
            print("message in key")
            print(parsed_message)
            datetime_object = datetime.now(_LOCAL_TZ)
            time_string = re.search("([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", parsed_message['message'])
            datetime_object = datetime.strptime(time_string.group(), '%Y-%m-%d %H:%M:%S')

        return {"response_type": "in_channel",
                "text": "<@{}> has started a {} `{}` model training run.  It's identifier will be *[{}]*".format(body['user_name'], PLATFORM, MODEL, datetime_object.strftime('%Y%m%d_%H%M%S'))}
