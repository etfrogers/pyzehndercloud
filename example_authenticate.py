import json
import logging
import urllib.parse

import msal

from pyzehndercloud import OAUTH2_CLIENT_ID
from pyzehndercloud.auth import OAUTH2_AUTHORITY, OAUTH2_REDIRECT_URL

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def run():
    # Create the msal app
    msal_app = msal.ConfidentialClientApplication(
        client_id=OAUTH2_CLIENT_ID,
        authority=OAUTH2_AUTHORITY,
        exclude_scopes=["profile"]
    )

    # Initiate the auth flow
    flow = msal_app.initiate_auth_code_flow(scopes=[OAUTH2_CLIENT_ID], redirect_uri=OAUTH2_REDIRECT_URL)
    print("Navigate to the following URL in a browser:")
    print(flow["auth_uri"])
    print()

    # Parse the reply
    print("Enter the URL you were redirected to, but don't continue on that page:")
    url = input()
    query_params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    if 'client_info' in query_params and query_params.get('client_info') == '1':
        del query_params['client_info']
    result = msal_app.acquire_token_by_auth_code_flow(flow, query_params) # , scopes=['df77b1ce-c368-4f7f-b0e6-c1406ac6bac9']

    if result.get("error"):
        print(
            "Error {}:\n{}".format(result.get("error"), result.get("error_description"))
        )
        exit(1)

    # Store the result in a file for later use
    with open(".auth_token.json", "w") as f:
        f.write(json.dumps(result))

    print(
        "Token acquired. You can now use the token in the auth header of your requests."
    )


if __name__ == "__main__":
    run()
