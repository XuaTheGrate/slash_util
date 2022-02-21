import discord
import slash_util

class SomeClass(slash_util.AutocompleteConverter):
    def __init__(self, value):
        self.value = value

    @classmethod
    def autocomplete(cls, ctx, arg):
        return [option for option in ["pog", "poggers", "pogchamp"] if option.startswith(arg)]

    @classmethod
    def convert(cls, ctx, arg):
        return cls(arg)

class SampleCog(slash_util.Cog):
    @slash_util.slash_command(guild_id=123)
    async def pog(self, ctx: slash_util.Context, some_option: int = 22, another_option: SomeClass = SomeClass("poggie")):
        await ctx.send(f"You entered: {some_option}, {another_option.value}", ephemeral=True)

    @pog.autocomplete_for("some_option")
    def autocomplete_some_option(self, ctx, value):
        return [1, 2, 3]

def setup(bot):
    bot.add_cog(SampleCog(bot))
