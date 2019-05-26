import os
import dotenv
import hug


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)
verification_token = os.environ['VERIFICATION_TOKEN']

@hug.get()
@hug.local()
def slash():
    """Post a message to a Slack User by UserId"""

    return {'text': "hello"}
