"""
A basic example for a dedicated file to import a signed in client everywhere else. For example in Cogs of discord bots.
To use the client in any other file use the following code:
```py
from import_client import abstractClient
coc_client = await abstractClient.get_client()
```
or
```py
from import_client import abstractClient
coc_client = await abstractClient.client
```

"""
import asyncio
import logging
from typing import AsyncGenerator

import coc
from coc import Client

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coc.http")
logger.setLevel(logging.DEBUG)


class AbstractClient:
	"""Class holding the async generator used to get the client and login on demand"""

	def __init__(self):
		# Pass credentials here or use a venv etc. to avoid hard coding them
		self.__async_gen = self.__yield_client()  # create the async generator

	async def __yield_client(self) -> AsyncGenerator[coc.Client, None]:
		"""Get the async generator which always yields the client"""

		async with coc.Client(loop=asyncio.get_event_loop_policy().get_event_loop()) as client:
			await client.login("EMAIL", "PASSWORD")  # be aware that hard coding credentials is bad practice!
			while True:
				try:
					yield client
				except GeneratorExit:
					break

	async def get_client(self) -> Client:
		"""Get the actual logged in client"""
		if not hasattr(self, '__async_gen') and not hasattr(self, '_AbstractClient__async_gen'):
			self.__async_gen = self.__yield_client()  # create async generator if needed
		coc_client = await self.__async_gen.__anext__()
		return coc_client

	@property
	async def client(self) -> Client:
		"""Get the actual logged in client"""
		if not hasattr(self, '__async_gen') and not hasattr(self, '_AbstractClient__async_gen'):
			self.__async_gen = self.__yield_client()  # create async generator if needed
		coc_client = await self.__async_gen.__anext__()
		return coc_client

	async def shutdown(self):
		"""Log out and close the ClientSession"""
		await self.__async_gen.aclose()


abstractClient = AbstractClient()
