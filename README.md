# slash_util is a simple wrapper around slash commands for discord.py
This is written by an official discord.py helper to try and stop people using third party forks or otherwise. If any help is required, please ping Maya#9000 in one of the help channels. To any other helpers reading this, this script is exempt from rule 14.

## Table of contents
- [Installation](#installation)
- [Defining parameters](#defining-parameters)
- [Ranges](#ranges)
- [Channels](#channels)
- [Examples](#examples)
- [API documentation](#api-documentation)

## Installation

**BEFORE ANYTHING** You must install discord.py 2.0 from GitHub:
```
pip install -U git+https://github.com/Rapptz/discord.py
```
This script will NOT work without it. See [this message](https://canary.discord.com/channels/336642139381301249/336642139381301249/859172828430336010) for more information on discord.py 2.0

You can now install slash_util from PyPI:
```
pip install -U slash-util
```

## Defining parameters
A few different parameter types can be specified in accordance with the discord api.

These parameters may only be used inside ``slash commands``, not within context menu commands.

- ``str`` for strings
- ``int`` or ``Range[min, max]`` for ints (see [Ranges](#ranges) for more information)
- ``float`` or ``Range[min, max]`` for floats (see [Ranges](#ranges) for more information)
- ``bool`` for booleans
- ``discord.User`` or ``discord.Member`` for members
- ``discord.Role`` for roles
- ``typing.Literal`` for option choices (see [Literals](#literals) for more information)

For defining channel parameters, they are documented in [Channels](#channels)

## Ranges
Ranges are a way to specify minimum and maximum values for ``ints`` and ``floats``. They can be defined inside a type hint, for example:
```python
@slash_util.slash_command()
async def my_command(self, ctx, number: slash_util.Range[0, 10]):
  # `number` will only be an int within this range
  await ctx.send(f"Your number was {number}!", ephemeral=True)
```
If you specify a float in either parameter, the value will be a float.

## Channels
Channels can be defined using ``discord.TextChannel``, ``VoiceChannel`` or ``CategoryChannel``.
You can specify multiple channel types via ``typing.Union``:
```python
@slash_util.slash_command()
async def my_command(self, ctx, channel: typing.Union[discord.TextChannel, discord.VoiceChannel]):
  await ctx.send(f'{channel.mention} is not a category!', ephemeral=True)
```

## Literals
A [typing.Literal](https://docs.python.org/3/library/typing.html#typing.Literal) is a special type hint that requires the passed parameter to be equal to one of the listed values.
The passed literals must be all the same type, which must be either ``str``, `int` or ``float``.
These will be used to create a list of options for the user to select from.
For example, given the following:

```python
from typing import Literal

@slash_util.slash_command()
async def shop(self, ctx, buy_sell: Literal['buy', 'sell'], amount: Literal[1, 2], item: str):
    await ctx.send(f'{buy_sell.capitalize()}ing {amount} {item}(s)!')
```
The ``buy_sell`` parameter must be either the literal string ``"buy"`` or ``"sell"`` and amount must be the int ``1`` or ``2``. 
## Examples
``slash_util`` defines a bot subclass to automatically handle posting updated commands to discords api. This isn't required but highly recommended to use.
```python
class MyBot(slash_util.Bot):
    def __init__(self):
        super().__init__(command_prefix="!")  # command prefix only applies to message based commands

        self.load_extension("cogs.my_cog")  # important!
        
if __name__ == '__main__':
    MyBot().run("token")
```
Sample cog:
```python
class MyCog(slash_util.Cog):
    @slash_util.slash_command()  # sample slash command
    async def slash(self, ctx: slash_util.Context, number: int):
        await ctx.send(f"You selected #{number}!", ephemeral=True)
    
    @slash_util.message_command(name="Quote")  # sample command for message context menus
    async def quote(self, ctx: slash_util.Context, message: discord.Message):  # these commands may only have a single Message parameter
        await ctx.send(f'> {message.clean_content}\n- {message.author}')
    
    @slash_util.user_command(name='Bonk')  # sample command for user context menus
    async def bonk(self, ctx: slash_util.Context, user: discord.Member):  # these commands may only have a single Member parameter
        await ctx.send(f'{ctx.author} BONKS {user} :hammer:')

def setup(bot):
    bot.add_cog(MyCog(bot))
```
See the api documentation below for more information on attributes, functions and more.

## API Documentation

##### ``deco @slash_command(**kwargs)``
Defines a function as a slash-type application command.

Parameters:
- name: ``str``
- - The display name of the command. If unspecified, will use the functions name.
- guild_id: ``Optional[int]``
- - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.
- description: ``str``
- - The description of the command. If unspecified, will use the functions docstring, or "No description provided" otherwise.

##### ``deco @message_command(**kwargs)``
Defines a function as a message-type application command.

Parameters:
- name: ``str``
- - The display name of the command. If unspecified, will use the functions name.
- guild_id: ``Optional[int]``
- - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.

##### ``deco @user_command(**kwargs)``
Defines a function as a user-type application command.

Parameters:
- name: ``str``
- - The display name of the command. If unspecified, will use the functions name.
- guild_id: ``Optional[int]``
- - The guild ID this command will belong to. If unspecified, the command will be uploaded globally.

##### ``deco @describe(**kwargs: str)``
Sets the description for the specified parameters of the slash command. Sample usage:
```python
@slash_util.slash_command()
@describe(channel="The channel to ping")
async def mention(self, ctx: slash_util.Context, channel: discord.TextChannel):
    await ctx.send(f'{channel.mention}')
```
If this decorator is not used, parameter descriptions will be set to "No description provided." instead.

##### ``class Range(min: NumT | None, max: NumT)``
Defines a minimum and maximum value for float or int values. The minimum value is optional.
```python
async def number(self, ctx, num: slash_util.Range[0, 10], other_num: slash_util.Range[10]):
    ...
```

##### ``class Bot(command_prefix, help_command=<default-help-command>, description=None, **options)``
None

Methods:

> ``get_application_command(self, name: str)``


Gets and returns an application command by the given name.

Parameters:
- name: ``str``
- - The name of the command.

Returns:
- [Command](#deco-slash_commandkwargs)
- - The relevant command object
- ``None``
- - No command by that name was found.


> ``async delete_all_commands(self, guild_id: int | None = None)``


Deletes all commands on the specified guild, or all global commands if no guild id was given.

Parameters:
- guild_id: ``Optional[str]``
- - The guild ID to delete from, or ``None`` to delete global commands.


> ``async delete_command(self, id: int, guild_id: int | None = None)``


Deletes a command with the specified ID. The ID is a snowflake, not the name of the command.

Parameters:
- id: ``int``
- - The ID of the command to delete.
- guild_id: ``Optional[str]``
- - The guild ID to delete from, or ``None`` to delete a global command.


> ``async sync_commands(self)``


Uploads all commands from cogs found and syncs them with discord.
Global commands will take up to an hour to update. Guild specific commands will update immediately.



##### ``class Context(bot: BotT, command: Command[CogT], interaction: discord.Interaction)``
The command interaction context.

Attributes
- bot: [``slash_util.Bot``](#class-botcommand_prefix-help_commanddefault-help-command-descriptionnone-options)
- - Your bot object.
- command: Union[[SlashCommand](#deco-slash_commandkwargs), [UserCommand](#deco-user_commandkwargs), [MessageCommand](deco-message_commandkwargs)]
- - The command used with this interaction.
- interaction: [``discord.Interaction``](https://discordpy.readthedocs.io/en/master/api.html#discord.Interaction)
- - The interaction tied to this context.

Methods:

> ``async send(self, content=..., **kwargs)``


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

Returns
- [``discord.InteractionMessage``](https://discordpy.readthedocs.io/en/master/api.html#discord.InteractionMessage) if this is the first time responding.
- [``discord.WebhookMessage``](https://discordpy.readthedocs.io/en/master/api.html#discord.WebhookMessage) for consecutive responses.

> ``async def defer(self, *, ephemeral: bool = False) -> None:``


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

> ``property cog(self)``

The cog this command belongs to.

> ``property guild(self)``

The guild this interaction was executed in.

> ``property message(self)``

The message that executed this interaction.

> ``property channel(self)``

The channel the interaction was executed in.

> ``property author(self)``

The user that executed this interaction.


##### ``class Cog(*args: Any, **kwargs: Any)``
The cog that must be used for application commands.

Attributes:
- bot: [``slash_util.Bot``](#class-botcommand_prefix-help_commanddefault-help-command-descriptionnone-options)
- - The bot instance.
