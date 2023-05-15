import asyncio
import json
import logging
import sys

import aiohttp

from pyzehndercloud.auth import InteractiveAuth
from pyzehndercloud.zehndercloud import ZehnderCloud

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Zehnder')


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
