import datetime
import json
import logging
import socket

import msal

from pyzehndercloud import OAUTH2_CLIENT_ID
from pyzehndercloud.auth import OAUTH2_AUTHORITY

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
    msal_app = msal.PublicClientApplication(
        client_id=OAUTH2_CLIENT_ID,
        authority=OAUTH2_AUTHORITY,
        exclude_scopes=["profile"]
    )

    result = msal_app.acquire_token_interactive(
        # Only works if your app is registered with redirect_uri as http://localhost
        [OAUTH2_CLIENT_ID],
        port=PORT,
        # parent_window_handle=...,  # If broker is enabled, you will be guided to provide a window handle
        # login_hint=config.get("username"),  # Optional.
        # If you know the username ahead of time, this parameter can pre-fill
        # the username (or email address) field of the sign-in page for the user,
        # Often, apps use this parameter during reauthentication,
        # after already extracting the username from an earlier sign-in
        # by using the preferred_username claim from returned id_token_claims.
        timeout=30,
        # prompt=msal.Prompt.SELECT_ACCOUNT,  # Or simply "select_account". Optional. It forces to show account selector page
        # prompt=msal.Prompt.CREATE,  # Or simply "create". Optional. It brings user to a self-service sign-up flow.
        # Prerequisite: https://docs.microsoft.com/en-us/azure/active-directory/external-identities/self-service-sign-up-user-flow
    )

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
