import asyncio
import atexit
import json
import logging
import os
import sys

import aiohttp
import msal
from aiohttp import ClientSession

from pyzehndercloud.auth import OAUTH2_CLIENT_ID, AbstractAuth, OAUTH2_AUTHORITY, OAUTH2_PORT
from pyzehndercloud.zehndercloud import ZehnderCloud

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Zehnder')


class InteractiveAuth(AbstractAuth):
    """This is an example implementation of the AbstractAuth class."""

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


async def main():
    with open('config.json') as file:
        config = json.load(file)
    async with aiohttp.ClientSession() as session:
        # Initialise ZehnderCloud API
        api = ZehnderCloud(session, InteractiveAuth(session, config['username'], config['api-key']))

        # Get a list of all devices
        devices = await api.get_devices()
        if len(devices) == 0:
            print("No devices found")
            sys.exit(1)

        # Get device state
        device = await api.get_device_state(devices[0])
        print(device)

        # Get device details
        device = await api.get_device_details(devices[0])
        print(device)

        device = await api.get_device_history(devices[0], valuename='runningMeanOutdoorTemparature')
        print(device)

        pass
        # # Set ventilation speed to away
        # await api.set_device_settings(
        #     devices[0], {"setVentilationPreset": {"value": 0}}
        # )
        #
        # # Sleep 5 seconds
        # await asyncio.sleep(5)
        #
        # # Set ventilation speed to low
        # await api.set_device_settings(
        #     devices[0], {"setVentilationPreset": {"value": 1}}
        # )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
