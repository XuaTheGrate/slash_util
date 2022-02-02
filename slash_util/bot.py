from __future__ import annotations

import inspect
from collections import defaultdict

from discord.ext import commands

from .cog import Cog
from .core import Command

__all__ = ['Bot']

class Bot(commands.Bot):
    application_id: int  # hack to avoid linting errors on http methods

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.login(token)
        
        app_info = await self.application_info()
        self._connection.application_id = app_info.id

        await self.sync_commands()
        await self.connect(reconnect=reconnect)

    def get_application_command(self, name: str) -> Command | None:
        """
        Gets and returns an application command by the given name.

        Parameters:
        - name: ``str``
        - - The name of the command.

        Returns:
        - [Command](#deco-slash_commandkwargs)
        - - The relevant command object
        - ``None``
        - - No command by that name was found.
        """

        for c in self.cogs.values():
            if isinstance(c, Cog):
                c = c._commands.get(name)
                if c:
                    return c

    async def delete_all_commands(self, guild_id: int | None = None):
        """
        Deletes all commands on the specified guild, or all global commands if no guild id was given.
        
        Parameters:
        - guild_id: ``Optional[str]``
        - - The guild ID to delete from, or ``None`` to delete global commands.
        """
        if guild_id is not None:
            await self.http.bulk_upsert_guild_commands(self.application_id, guild_id, [])
        else:
            await self.http.bulk_upsert_global_commands(self.application_id, [])

    async def delete_command(self, id: int, *, guild_id: int | None = None):
        """
        Deletes a command with the specified ID. The ID is a snowflake, not the name of the command.
        
        Parameters:
        - id: ``int``
        - - The ID of the command to delete.
        - guild_id: ``Optional[str]``
        - - The guild ID to delete from, or ``None`` to delete a global command.
        """
        if guild_id is not None:
            await self.http.delete_guild_command(self.application_id, guild_id, id)
        else:
            await self.http.delete_global_command(self.application_id, id)

    async def sync_commands(self) -> None:
        """
        Uploads all commands from cogs found and syncs them with discord.
        Global commands will take up to an hour to update. Guild specific commands will update immediately.
        """
        if not self.application_id:
            raise RuntimeError("sync_commands must be called after `run`, `start` or `login`")

        command_payloads = defaultdict(list)
        for cog in self.cogs.values():
            if not isinstance(cog, Cog):
                continue
                
            if not hasattr(cog, "_commands"):
                cog._commands = {}

            slashes = inspect.getmembers(cog, lambda c: isinstance(c, Command))
            for _, cmd in slashes:
                cmd.cog = cog
                cog._commands[cmd.name] = cmd
                body = cmd._build_command_payload()
                command_payloads[cmd.guild_id].append(body)

        global_commands = command_payloads.pop(None, [])
        if global_commands:
            await self.http.bulk_upsert_global_commands(self.application_id, global_commands)

        for guild_id, payload in command_payloads.items():
            await self.http.bulk_upsert_guild_commands(self.application_id, guild_id, payload)
