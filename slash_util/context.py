from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, overload

import discord
from discord.utils import MISSING

from .core import Command

BotT = TypeVar("BotT", bound='Bot')
CogT = TypeVar("CogT", bound='Cog')
CtxT = TypeVar("CtxT", bound='Context')

if TYPE_CHECKING:
    from typing import Any, Coroutine, Union
    from .bot import Bot
    from .cog import Cog
    from .modal import Modal
    from ._patch import InteractionResponse
    

__all__ = ['Context']

class Context(Generic[BotT, CogT]):
    """
    The command interaction context.
    
    Attributes
    - bot: [``slash_util.Bot``](#class-botcommand_prefix-help_commanddefault-help-command-descriptionnone-options)
    - - Your bot object.
    - command: Union[[SlashCommand](#deco-slash_commandkwargs), [UserCommand](#deco-user_commandkwargs), [MessageCommand](deco-message_commandkwargs)]
    - - The command used with this interaction.
    - interaction: [``discord.Interaction``](https://discordpy.readthedocs.io/en/master/api.html#discord.Interaction)
    - - The interaction tied to this context."""
    def __init__(self, bot: BotT, command: Command[CogT], interaction: discord.Interaction):
        self.bot = bot
        self.command = command
        self.interaction = interaction
    
    @property
    def response(self) -> InteractionResponse:
        return self.interaction.response  # type: ignore

    @overload
    def send(self, content: str = MISSING, *, embed: discord.Embed = MISSING, ephemeral: bool = MISSING, tts: bool = MISSING, view: discord.ui.View = MISSING, file: discord.File = MISSING) -> Coroutine[Any, Any, Union[discord.InteractionMessage, discord.WebhookMessage]]: ...

    @overload
    def send(self, content: str = MISSING, *, embed: discord.Embed = MISSING, ephemeral: bool = MISSING, tts: bool = MISSING, view: discord.ui.View = MISSING, files: list[discord.File] = MISSING) -> Coroutine[Any, Any, Union[discord.InteractionMessage, discord.WebhookMessage]]: ...

    @overload
    def send(self, content: str = MISSING, *, embeds: list[discord.Embed] = MISSING, ephemeral: bool = MISSING, tts: bool = MISSING, view: discord.ui.View = MISSING, file: discord.File = MISSING) -> Coroutine[Any, Any, Union[discord.InteractionMessage, discord.WebhookMessage]]: ...

    @overload
    def send(self, content: str = MISSING, *, embeds: list[discord.Embed] = MISSING, ephemeral: bool = MISSING, tts: bool = MISSING, view: discord.ui.View = MISSING, files: list[discord.File] = MISSING) -> Coroutine[Any, Any, Union[discord.InteractionMessage, discord.WebhookMessage]]: ...

    @overload
    def send(self, *, modal: Modal = MISSING) -> Coroutine[Any, Any, None]:
        ...

    async def send(self, content = MISSING, **kwargs):
        """
        Responds to the given interaction. If you have responded already, this will use the follow-up webhook instead.
        Parameters ``embed`` and ``embeds`` cannot be specified together.
        Parameters ``file`` and ``files`` cannot be specified together.
        
        Parameters:
        - content: ``str``
        - - The content of the message to respond with
        - embed: [``discord.Embed``](https://discordpy.readthedocs.io/en/master/api.html#discord.Embed)
        - - An embed to send with the message. Incompatible with ``embeds``.
        - embeds: ``List[``[``discord.Embed``](https://discordpy.readthedocs.io/en/master/api.html#discord.Embed)``]``
        - - A list of embeds to send with the message. Incompatible with ``embed``.
        - file: [``discord.File``](https://discordpy.readthedocs.io/en/master/api.html#discord.File)
        - - A file to send with the message. Incompatible with ``files``.
        - files: ``List[``[``discord.File``](https://discordpy.readthedocs.io/en/master/api.html#discord.File)``]``
        - - A list of files to send with the message. Incompatible with ``file``.
        - ephemeral: ``bool``
        - - Whether the message should be ephemeral (only visible to the interaction user).
        - - Note: This field is ignored if the interaction was deferred.
        - tts: ``bool``
        - - Whether the message should be played via Text To Speech. Send TTS Messages permission is required.
        - view: [``discord.ui.View``](https://discordpy.readthedocs.io/en/master/api.html#discord.ui.View)
        - - Components to attach to the sent message.

        Returns
        - [``discord.InteractionMessage``](https://discordpy.readthedocs.io/en/master/api.html#discord.InteractionMessage) if this is the first time responding.
        - [``discord.WebhookMessage``](https://discordpy.readthedocs.io/en/master/api.html#discord.WebhookMessage) for consecutive responses.
        """
        if 'modal' in kwargs:
            return await self._send_modal(modal=kwargs['modal'])

        if self.response.is_done():
            return await self.interaction.followup.send(content, wait=True, **kwargs)

        await self.response.send_message(content or None, **kwargs)

        return await self.interaction.original_message()

    async def _send_modal(self, modal: Modal):
        await self.response.send_modal(modal=modal)

    async def defer(self, *, ephemeral: bool = False) -> None:
        """
        Defers the given interaction.

        This is done to acknowledge the interaction.
        A secondary action will need to be sent within 15 minutes through the follow-up webhook.

        Parameters:
        - ephemeral: ``bool``
        - - Indicates whether the deferred message will eventually be ephemeral. Defaults to `False`

        Returns
        - ``None``

        Raises
        - [``discord.HTTPException``](https://discordpy.readthedocs.io/en/master/api.html#discord.HTTPException)
        - - Deferring the interaction failed.
        - [``discord.InteractionResponded``](https://discordpy.readthedocs.io/en/master/api.html#discord.InteractionResponded)
        - - This interaction has been responded to before.
        """
        await self.interaction.response.defer(ephemeral=ephemeral)
    
    @property
    def cog(self) -> CogT:
        """The cog this command belongs to."""
        return self.command.cog

    @property
    def guild(self) -> discord.Guild:
        """The guild this interaction was executed in."""
        return self.interaction.guild  # type: ignore

    @property
    def message(self) -> discord.Message:
        """The message that executed this interaction."""
        return self.interaction.message  # type: ignore

    @property
    def channel(self) -> discord.interactions.InteractionChannel:
        """The channel the interaction was executed in."""
        return self.interaction.channel  # type: ignore

    @property
    def author(self) -> discord.Member:
        """The user that executed this interaction."""
        return self.interaction.user  # type: ignore
