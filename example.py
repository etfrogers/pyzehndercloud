import asyncio
import json
import logging
import sys

import aiohttp
from aiohttp import ClientSession

from pyzehndercloud.auth import OAUTH2_CLIENT_ID, OAUTH2_TOKEN_URL, AbstractAuth
from pyzehndercloud.zehndercloud import ZehnderCloud

logging.basicConfig(level=logging.DEBUG)

_LOGGER = logging.getLogger(__name__)


class ExampleAuth(AbstractAuth):
    """This is an example implementation of the AbstractAuth class."""

    def __init__(self, websession: ClientSession):
        super().__init__(websession)

        # Load .auth_token.json
        with open(".auth_token.json", "r") as f:
            self._tokens = json.load(f)

        if not self._tokens:
            print(
                "Please provide a valid auth_token.json file. You can create one by running example_authenticate.py."
            )
            sys.exit(1)

    async def async_get_access_token(self) -> str:
        """Returns a token that can be used to authenticate against the API.
        Note that this is an example, you probably want to cache the access_token, and only refresh it when it
        expires.
        """
        # Refresh token if it has expired
        form = {
            "client_id": OAUTH2_CLIENT_ID,
            "scope": "openid profile offline_access",
            "grant_type": "refresh_token",
            "refresh_token": self._tokens.get("refresh_token"),
        }
        async with self.websession.post(OAUTH2_TOKEN_URL, data=form) as response:
            if response.status != 200:
                error = await response.json()
                raise Exception(error.get("error_description"))

            data = await response.json()
            return data.get("id_token")


async def main():
    async with aiohttp.ClientSession() as session:
        # Initialise ZehnderCloud API
        api = ZehnderCloud(session, ExampleAuth(session))

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
