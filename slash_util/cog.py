from __future__ import annotations

import traceback
import sys
from typing import TYPE_CHECKING, Generic, TypeVar

import discord
from discord.ext import commands


from .context import Context
from .core import Command

BotT = TypeVar("BotT", bound='Bot')

if TYPE_CHECKING:
    from .bot import Bot
    from .modal import Modal
    from typing import Awaitable, Any, Callable
    from typing_extensions import Self, ParamSpec, Concatenate

    WrapperPS = ParamSpec("WrapperPS")

__all__ = ['Cog']

async def command_error_wrapper(func: Callable[WrapperPS, Awaitable[Any]], *args: WrapperPS.args, **kwargs: WrapperPS.kwargs) -> Any:
    try:
        return await func(*args, **kwargs)
    except commands.CommandError:
        raise
    except Exception as e:
        raise commands.CommandInvokeError(e) from e

class Cog(commands.Cog, Generic[BotT]):
    """
    The cog that must be used for application commands.
    
    Attributes:
    - bot: [``slash_util.Bot``](#class-botcommand_prefix-help_commanddefault-help-command-descriptionnone-options)
    - - The bot instance."""
    def __init__(self, bot: BotT):
        self.bot: BotT = bot
        self._commands: dict[str, Command]
    
    async def slash_command_error(self, ctx: Context[BotT, Self], error: Exception) -> None:
        print("Error occured in command", ctx.command.name, file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__)

    @commands.Cog.listener("on_interaction")
    async def _internal_interaction_handler(self, interaction: discord.Interaction):
        if interaction.type.value == 5:  # MODAL_SUBMIT
            if not hasattr(self.bot._connection, '_modals'):
                self.bot._connection._modals = {}  # type: ignore

            custom_id = interaction.data['custom_id']  # type: ignore
            modal: Modal | None = self.bot._connection._modals.pop(custom_id, None)  # type: ignore
            if modal is not None:
                modal._response.set_result(interaction)
            return

        if interaction.type is not discord.InteractionType.application_command:
            return
            
        name = interaction.data['name']  # type: ignore
        command = self._commands.get(name)
        
        if not command:
            return

        state = self.bot._connection
        params: dict = command._build_arguments(interaction, state)
        
        ctx = Context(self.bot, command, interaction)
        try:
            await command_error_wrapper(command.invoke, ctx, **params)
        except commands.CommandError as e:
            await self.slash_command_error(ctx, e)
