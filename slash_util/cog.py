from __future__ import annotations

import traceback
import sys
from typing import TYPE_CHECKING, Generic, TypeVar

import discord
from discord.ext import commands

BotT = TypeVar("BotT", bound='Bot')

if TYPE_CHECKING:
    from .bot import Bot
    from .core import Command
    from .context import Context
    
    from typing_extensions import Self

__all__ = ['Cog']

class Cog(commands.Cog):
    """
    The cog that must be used for application commands.
    """
    _commands: dict[str, Command[Self]]

    async def slash_command_error(self, ctx: Context[BotT, Self], error: Exception) -> None:
        print("Error occured in command", ctx.command.name, file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__)
