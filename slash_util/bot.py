from __future__ import annotations

import inspect
from collections import defaultdict
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .cog import Cog
from .core import Command
from .context import Context

if TYPE_CHECKING:
    from .modal import Modal
    from typing import Awaitable, Any, Callable
    from typing_extensions import ParamSpec

    WrapperPS = ParamSpec("WrapperPS")

__all__ = ['Bot']

async def command_error_wrapper(func: Callable[WrapperPS, Awaitable[Any]], *args: WrapperPS.args, **kwargs: WrapperPS.kwargs) -> Any:
    try:
        return await func(*args, **kwargs)
    except commands.CommandError:
        raise
    except Exception as e:
        raise commands.CommandInvokeError(e) from e

class Bot(commands.AutoShardedBot):
    application_id: int  # hack to avoid linting errors on http methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_listener(self._internal_interaction_handler, "on_interaction")

    async def _internal_interaction_handler(self, interaction: discord.Interaction):
        if interaction.type.value == 5:  # MODAL_SUBMIT
            if not hasattr(self._connection, '_modals'):
                self.bot._connection._modals = {}  # type: ignore

            custom_id = interaction.data['custom_id']  # type: ignore
            modal: Modal | None = self.bot._connection._modals.pop(custom_id, None)  # type: ignore
            if modal is not None:
                modal._response.set_result(interaction)
            return

        if interaction.type is not discord.InteractionType.application_command:
            return
            
        name = interaction.data['name']  # type: ignore
        command = self.get_application_command(name)
        
        if not command:
            return
        
        cog = command.cog

        state = self._connection
        params: dict = command._build_arguments(interaction, state)
        
        ctx = Context(self, command, interaction)
        try:
            await command_error_wrapper(command.invoke, ctx, **params)
        except commands.CommandError as e:
            await cog.slash_command_error(ctx, e)

    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        if isinstance(cog, Cog) and not hasattr(cog, "_commands"):
            cog._commands = {}  # type: ignore

        super().add_cog(cog, override=override)

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

    async def reload_all_extensions(self) -> None:
        """
        Collects all loaded extensions and reloads them, synchronizing the application commands in the process.
        """
        exts = list(self.extensions)
        for item in exts:
            self.reload_extension(item)
        
        await self.sync_commands()

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
