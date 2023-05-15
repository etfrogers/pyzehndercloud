import atexit
import os
from abc import ABC, abstractmethod

import msal
from aiohttp import ClientSession

from example import logger

TENANT = 'zehndergroupauth'
POLICY = 'B2C_1_signin_signup_enduser'
OAUTH2_AUTHORITY = f"https://{TENANT}.b2clogin.com/{TENANT}.onmicrosoft.com/{POLICY}"
OAUTH2_AUTHORIZE_URL = f"{OAUTH2_AUTHORITY}/oauth2/v2.0/authorize"
OAUTH2_TOKEN_URL = f"{OAUTH2_AUTHORITY}/oauth2/v2.0/token"

OAUTH2_PORT = 5000
OAUTH2_REDIRECT_URL = f"http://localhost:{OAUTH2_PORT}"

OAUTH2_CLIENT_ID = 'df77b1ce-c368-4f7f-b0e6-c1406ac6bac9'  # Documentation


class AuthError(Exception):
    """Authentication has failed."""


class AbstractAuth(ABC):
    """Abstract class to make authenticated requests."""

    def __init__(self, websession: ClientSession, api_key: str):
        """Initialize the auth."""
        self.websession = websession
        self.api_key = api_key

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""


class InteractiveAuth(AbstractAuth):
    """This is an  implementation of the AbstractAuth class that uses pymsal's interactive auth flow"""

    def __init__(self, websession: ClientSession, api_key: str, username: str):
        super().__init__(websession, api_key)
        self.username = username
        cache = msal.SerializableTokenCache()
        if os.path.exists("my_cache.json"):
            cache.deserialize(open("my_cache.json", "r").read())
        atexit.register(lambda:
                        open("my_cache.json", "w").write(cache.serialize())
                        # Hint: The following optional line persists only when state changed
                        if cache.has_state_changed else None
                        )
        self.app = msal.PublicClientApplication(
            OAUTH2_CLIENT_ID, authority=OAUTH2_AUTHORITY,
            exclude_scopes=["profile"],
            token_cache=cache,
        )

    async def async_get_access_token(self) -> str:
        """Returns a token that can be used to authenticate against the API.
        Note that this is an example, you probably want to cache the access_token, and only refresh it when it
        expires.
        """
        accounts = self.app.get_accounts(username=self.username)
        result = None
        if accounts:
            logger.info("Account(s) exists in cache, probably with token too. Let's try.")
            logger.info("Account(s) already signed in:")
            for a in accounts:
                logger.debug(a["username"])
            chosen = accounts[0]  # Assuming the end user chose this one to proceed
            logger.info("Proceed with account: %s" % chosen["username"])
            # Now let's try to find a token in cache for this account
            result = self.app.acquire_token_silent([OAUTH2_CLIENT_ID], account=chosen)

        if not result:
            result = self.app.acquire_token_interactive(
                [OAUTH2_CLIENT_ID],
                port=OAUTH2_PORT,
                # login_hint=config.get("username"),  # Optional.
                # If you know the username ahead of time, this parameter can pre-fill
                # the username (or email address) field of the sign-in page for the user,
                # Often, apps use this parameter during reauthentication,
                # after already extracting the username from an earlier sign-in
                # by using the preferred_username claim from returned id_token_claims.
                timeout=30,
            )
        return result['id_token']
