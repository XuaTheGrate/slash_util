from __future__ import annotations

import inspect
from collections import defaultdict
from typing import TYPE_CHECKING, TypeVar, overload, Union, Generic, get_origin, get_args, Literal

import discord, discord.state

NumT = Union[int, float]

CtxT = TypeVar("CtxT", bound='Context')
BotT = TypeVar("BotT", bound='Bot')
CogT = TypeVar("CogT", bound='Cog')

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable, ClassVar
    from typing_extensions import Concatenate, ParamSpec

    from .bot import Bot
    from .cog import Cog
    from .context import Context

    CmdP = ParamSpec("CmdP")
    CmdT = Callable[Concatenate[CogT, CtxT, CmdP], Awaitable[Any]]
    MsgCmdT = Callable[[CogT, CtxT, discord.Message], Awaitable[Any]]
    UsrCmdT = Callable[[CogT, CtxT, discord.Member], Awaitable[Any]]
    CtxMnT = Union[MsgCmdT, UsrCmdT]

    RngT = TypeVar("RngT", bound="Range")

__all__ = ['describe', 'slash_command', 'message_command', 'user_command', 'Range', 'Command', 'SlashCommand', 'ContextMenuCommand', 'UserCommand', 'MessageCommand']
def _parse_resolved_data(interaction: discord.Interaction, data, state: discord.state.ConnectionState):
    if not data:
        return {}

    assert interaction.guild 
    resolved = {}

    resolved_users = data.get('users')
    if resolved_users:
        resolved_members = data['members']
        for id, d in resolved_users.items():
            member_data = resolved_members[id]
            member_data['user'] = d
            member = discord.Member(data=member_data, guild=interaction.guild, state=state)
            resolved[int(id)] = member
        
    resolved_channels = data.get('channels')
    if resolved_channels:
        for id, d in resolved_channels.items():
            d['position'] = None
            cls, _ = discord.channel._guild_channel_factory(d['type'])
            channel = cls(state=state, guild=interaction.guild, data=d)
            resolved[int(id)] = channel

    resolved_messages = data.get('messages')
    if resolved_messages:
        for id, d in resolved_messages.items():
            msg = discord.Message(state=state, channel=interaction.channel, data=d)  # type: ignore
            resolved[int(id)] = msg

    resolved_roles = data.get('roles')
    if resolved_roles:
        for id, d in resolved_roles.items():
            role = discord.Role(guild=interaction.guild, state=state, data=d)
            resolved[int(id)] = role
         
    resolved_attachments = data.get('attachments')
    if resolved_attachments:
        for id, d in resolved_attachments.items():
            attachment = discord.Attachment(state=state, data=d)
            resolved[int(id)] = attachment
            

    return resolved

command_type_map: dict[type[Any], int] = {
    str: 3,
    int: 4,
    bool: 5,
    discord.User: 6,
    discord.Member: 6,
    discord.TextChannel: 7,
    discord.VoiceChannel: 7,
    discord.CategoryChannel: 7,
    discord.Role: 8,
    float: 10,
    discord.Attachment: 11
}

channel_filter: dict[type[discord.abc.GuildChannel], int] = {
    discord.TextChannel: 0,
    discord.VoiceChannel: 2,
    discord.CategoryChannel: 4
}

def describe(**kwargs):
    """
    Sets the description for the specified parameters of the slash command. Sample usage:
    ```python
    @slash_util.slash_command()
    @describe(channel="The channel to ping")
    async def mention(self, ctx: slash_util.Context, channel: discord.TextChannel):
        await ctx.send(f'{channel.mention}')
    ```
    If this decorator is not used, parameter descriptions will be set to "No description provided." instead."""
    def _inner(cmd):
        func = cmd.func if isinstance(cmd, SlashCommand) else cmd
        for name, desc in kwargs.items():
            try:
                func._param_desc_[name] = desc
            except AttributeError:
                func._param_desc_ = {name: desc}
        return cmd
    return _inner

def slash_command(**kwargs) -> Callable[[CmdT], SlashCommand]:
    """
    Defines a function as a slash-type application command.
    
    Parameters:
    - name: ``str``
    - - The display name of the command. If unspecified, will use the functions name.
    - guild_id: ``Optional[int]``
    - - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.
    - description: ``str``
    - - The description of the command. If unspecified, will use the functions docstring, or "No description provided" otherwise.
    """
    def _inner(func: CmdT) -> SlashCommand:
        return SlashCommand(func, **kwargs)
    return _inner
    
def message_command(**kwargs) -> Callable[[MsgCmdT], MessageCommand]:
    """
    Defines a function as a message-type application command.
    
    Parameters:
    - name: ``str``
    - - The display name of the command. If unspecified, will use the functions name.
    - guild_id: ``Optional[int]``
    - - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.
    """
    def _inner(func: MsgCmdT) -> MessageCommand:
        return MessageCommand(func, **kwargs)
    return _inner

def user_command(**kwargs) -> Callable[[UsrCmdT], UserCommand]:
    """
    Defines a function as a user-type application command.
    
    Parameters:
    - name: ``str``
    - - The display name of the command. If unspecified, will use the functions name.
    - guild_id: ``Optional[int]``
    - - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.
    """
    def _inner(func: UsrCmdT) -> UserCommand:
        return UserCommand(func, **kwargs)
    return _inner

class _RangeMeta(type):
    @overload
    def __getitem__(cls: type[RngT], max: int) -> type[int]: ...
    @overload
    def __getitem__(cls: type[RngT], max: tuple[int, int]) -> type[int]: ...
    @overload
    def __getitem__(cls: type[RngT], max: float) -> type[float]: ...
    @overload
    def __getitem__(cls: type[RngT], max: tuple[float, float]) -> type[float]: ...

    def __getitem__(cls, max):
        if isinstance(max, tuple):
            return cls(*max)
        return cls(None, max)

class Range(metaclass=_RangeMeta):
    """
    Defines a minimum and maximum value for float or int values. The minimum value is optional.
    ```python
    async def number(self, ctx, num: slash_util.Range[0, 10], other_num: slash_util.Range[10]):
        ...
    ```"""
    def __init__(self, min: NumT | None, max: NumT):
        if min is not None and min >= max:
            raise ValueError("`min` value must be lower than `max`")
        self.min = min
        self.max = max

class Command(Generic[CogT]):
    cog: CogT
    func: Callable
    name: str
    guild_id: int | None

    def _build_command_payload(self) -> dict[str, Any]:
        raise NotImplementedError

    def _build_arguments(self, interaction: discord.Interaction, state: discord.state.ConnectionState) -> dict[str, Any]:
        raise NotImplementedError

    async def invoke(self, context: Context[BotT, CogT], **params) -> None:
        await self.func(self.cog, context, **params)

class SlashCommand(Command[CogT]):
    def __init__(self, func: CmdT, **kwargs):
        self.func = func
        self.cog: CogT

        self.name: str = kwargs.get("name", func.__name__)

        self.description: str = kwargs.get("description") or func.__doc__ or "No description provided"

        self.guild_id: int | None = kwargs.get("guild_id")

        self.parameters = self._build_parameters()
        self._parameter_descriptions: dict[str, str] = defaultdict(lambda: "No description provided")

    def _build_arguments(self, interaction, state):
        if 'options' not in interaction.data:
            return {}

        resolved = _parse_resolved_data(interaction, interaction.data.get('resolved'), state)
        result = {}
        for option in interaction.data['options']:
            value = option['value']
            if option['type'] in (6, 7, 8):
                value = resolved[int(value)]

            result[option['name']] = value
        return result

    def _build_parameters(self) -> dict[str, inspect.Parameter]:
        params = list(inspect.signature(self.func).parameters.values())
        try:
            params.pop(0)
        except IndexError:
            raise ValueError("expected argument `self` is missing")
        
        try:
            params.pop(0)
        except IndexError:
            raise ValueError("expected argument `context` is missing")

        return {p.name: p for p in params}

    def _build_descriptions(self):
        if not hasattr(self.func, '_param_desc_'):
            return
        
        for k, v in self.func._param_desc_.items():
            if k not in self.parameters:
                raise TypeError(f"@describe used to describe a non-existant parameter `{k}`")

            self._parameter_descriptions[k] = v

    def _build_command_payload(self):
        self._build_descriptions()

        payload = {
            "name": self.name,
            "description": self.description,
            "type": 1
        }

        params = self.parameters
        if params:
            options = []
            for name, param in params.items():
                ann = param.annotation

                if ann is param.empty:
                    raise TypeError(f"missing type annotation for parameter `{param.name}` for command `{self.name}`")

                if isinstance(ann, str):
                    ann = eval(ann)

                if isinstance(ann, Range):
                    real_t = type(ann.max)
                elif get_origin(ann) is Union:
                    args = get_args(ann)
                    real_t = args[0]
                elif get_origin(ann) is Literal:
                    real_t = type(ann.__args__[0])
                else:
                    real_t = ann
                    print(real_t)

                typ = command_type_map[real_t]
                option = {
                    'type': typ,
                    'name': name,
                    'description': self._parameter_descriptions[name]
                }
                if param.default is param.empty:
                    option['required'] = True
                
                if isinstance(ann, Range):
                    option['max_value'] = ann.max
                    option['min_value'] = ann.min

                elif get_origin(ann) is Union:
                    args = get_args(ann)

                    if not all(issubclass(k, discord.abc.GuildChannel) for k in args):
                        raise TypeError(f"Union parameter types only supported on *Channel types")

                    if len(args) != 3:
                        filtered = [channel_filter[i] for i in args]
                        option['channel_types'] = filtered

                elif get_origin(ann) is Literal:
                    arguments = ann.__args__
                    option['choices'] = [{'name': str(a), 'value': a} for a in arguments]

                elif issubclass(ann, discord.abc.GuildChannel):
                    option['channel_types'] = [channel_filter[ann]]
                
                options.append(option)
            options.sort(key=lambda f: not f.get('required'))
            payload['options'] = options
        return payload

class ContextMenuCommand(Command[CogT]):
    _type: ClassVar[int]

    def __init__(self, func: CtxMnT, **kwargs):
        self.func = func
        self.guild_id: int | None = kwargs.get('guild_id', None)
        self.name: str = kwargs.get('name', func.__name__)

    def _build_command_payload(self):
        payload = {
            'name': self.name,
            'type': self._type
        }
        if self.guild_id is not None:
            payload['guild_id'] = self.guild_id
        return payload

    def _build_arguments(self, interaction: discord.Interaction, state: discord.state.ConnectionState) -> dict[str, Any]:
        resolved = _parse_resolved_data(interaction, interaction.data.get('resolved'), state)  # type: ignore
        value = resolved[int(interaction.data['target_id'])]  # type: ignore
        return {'target': value}

    async def invoke(self, context: Context[BotT, CogT], **params) -> None:
        await self.func(self.cog, context, *params.values())

class MessageCommand(ContextMenuCommand[CogT]):
    _type = 3

class UserCommand(ContextMenuCommand[CogT]):
    _type = 2
