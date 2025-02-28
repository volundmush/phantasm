import asyncio

from rich.console import Console

import mudpy

from mudpy.portal.link import Link as OldLink

class Link(OldLink):

    def __init__(self, session: "GameSession"):
        super().__init__(session)
        self.console = Console(color_system="standard", file=self, record=True,
                               width=self.session.capabilities.width,
                               height=self.session.capabilities.height)
        self.console._color_system = self.session.capabilities.color

    def flush(self):
        """
        Used for compatability.
        """

    def write(self, data):
        """
        Used for compatability.
        """

    def print(self, *args, **kwargs) -> str:
        """
        A thin wrapper around Rich.Console's print. Returns the exported data.
        """
        new_kwargs = {"highlight": False}
        new_kwargs.update(kwargs)
        new_kwargs["end"] = "\r\n"
        new_kwargs["crop"] = False
        self.console.print(*args, **new_kwargs)
        return self.console.export_text(clear=True, styles=True)

    async def send_rich(self, *args, **kwargs):
        """
        Sends a Rich message to the client.
        """
        out = self.print(*args, **kwargs)
        await self.session.handle_send_text(out)

    async def send_text(self, text: str):
        """
        Sends plain text to the client.
        """
        await self.session.handle_send_text(text)