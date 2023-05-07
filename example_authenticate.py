import datetime
import json
import logging
import socket
import urllib.parse

import msal

from pyzehndercloud import OAUTH2_CLIENT_ID
from pyzehndercloud.auth import OAUTH2_AUTHORITY, OAUTH2_REDIRECT_URL

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

HOST = 'localhost'
PORT = 5000


def listen_on_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        received = b''
        start_time = datetime.datetime.now()
        timeout = start_time + datetime.timedelta(seconds=5)
        with conn:
            print(f"Connected by {addr}")
            while datetime.datetime.now() < timeout:
                data = conn.recv(1024)
                print(data)
                if not data:
                    break
                received += data
    return received


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

    request_data = listen_on_socket()
    request_str = request_data.decode("utf-8")
    get, url, *tokens = request_str.split()

    query_params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    if 'client_info' in query_params and query_params.get('client_info') == '1':
        del query_params['client_info']
    result = msal_app.acquire_token_by_auth_code_flow(flow, query_params)

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
