# slash_util is a library that adds new features to discord.py

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

## Features
- [Application Commands (slash commands + message/user context menu commands)](#application-commands)
- [New Modal interaction](#modals)

## Application Commands

### Defining parameters
A few different parameter types can be specified in accordance with the discord api.

These parameters may only be used inside ``slash commands``, not within context menu commands.

- ``str`` for strings
- ``int`` or ``Range[min, max]`` for ints (see [Ranges](#ranges) for more information)
- ``float`` or ``Range[min, max]`` for floats (see [Ranges](#ranges) for more information)
- ``bool`` for booleans
- ``discord.User`` or ``discord.Member`` for members
- ``discord.Role`` for roles
- ``discord.Attachment`` for attaching files (see [Attachments](#attachments) for more information)
- ``typing.Literal`` for option choices (see [Literals](#literals) for more information)

For defining channel parameters, they are documented in [Channels](#channels)

Parameters can also be optional, see [Optional](#optional)

### Ranges
Ranges are a way to specify minimum and maximum values for ``ints`` and ``floats``. They can be defined inside a type hint, for example:
```python
@slash_util.slash_command()
async def my_command(self, ctx, number: slash_util.Range[0, 10]):
  # `number` will only be an int within this range
  await ctx.send(f"Your number was {number}!", ephemeral=True)
```
If you specify a float in either parameter, the value will be a float.

### Channels
Channels can be defined using ``discord.TextChannel``, ``VoiceChannel`` or ``CategoryChannel``.
You can specify multiple channel types via ``typing.Union``:
```python
@slash_util.slash_command()
async def my_command(self, ctx, channel: typing.Union[discord.TextChannel, discord.VoiceChannel]):
  await ctx.send(f'{channel.mention} is not a category!', ephemeral=True)
```

### Attachments
NEW: Discord now lets you upload attachments to slash commands. ``slash_util`` supports this via the ``discord.Attachment`` type hint, for example:
```python
@slash_util.slash_command()
async def my_command(self, ctx, attachment: discord.Attachment):
    await ctx.send("Your file:", file=await attachment.to_file())
```

### Literals
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

### Optional
A parameter can be optional by assigning a default value to it.

```python
@slash_util.slash_command()
async def add(self, ctx, a: int, b: int, c: int = 0):
    total = a + b + c
    await ctx.send(f"{a} + {b} + {c} = {total}")
```
If the `c` parameter isn't given, it will be defaulted to 0. This will also show up to the user as an optional argument.

The default value isn't type restricted as well, this is to support `None` types but this could be used to give any other type. This means the above example can be rewritten in two ways -

```python
@slash_util.slash_command()
async def add(self, ctx, a: int, b: int, c: int = None):
    ...

@slash_util.slash_command()
async def add(self, ctx, a: int, b: int, c: int = '0'):
    ...
```
Same as before, only the `c` parameter will give a different value in the two examples. The first one will give `None` and the second will give a string `'0'`. If the user gives `c` then it is restricted to integers.

## Modals

Discord recently added a new interaction type - Modals. These aren't supported with discord.py, and I've decided to implement them in my library.
```python
import slash_util

@slash_util.slash_command()
async def modal(self, ctx):
    modal = slash_util.Modal(title="Hello, world!", items=[
        slash_util.TextInput(custom_id="name", label="What is your name?", style=slash_util.TextInputStyle.short),  # custom_id is important!
        slash_util.TextInput(custom_id="about", label="Tell us about yourself!", style=slash_util.TextInputStyle.paragraph)
    ])
    await ctx.send(modal=modal)

    try:
        interaction = await modal.wait(timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("You didn't respond in time...")
        return
    
    response = modal.response  # this will be a dict with the custom_ids above as the keys, and the user responses as the values
    name = response['name']
    await interaction.response.send_message(f"Hello, {name}!")
```

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
