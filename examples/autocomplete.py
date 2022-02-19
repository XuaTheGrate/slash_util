import discord
import slash_util

def example_autocomplete_handler(ctx: slash_util.Context, arg: str) -> list[str]:
    return [option for option in ["pog", "poggers", "pogchamp"] if option.startswith(arg)]

class SampleCog(slash_util.Cog):
    @slash_util.slash_command(guild_id=123)
    @slash_util.autocomplete("some_option", example_autocomplete_handler)
    async def pog(self, ctx: slash_util.Context, some_option: str = "poggers"):
        await ctx.send(f"You entered: {some_option}", ephemeral=True)

def setup(bot):
    bot.add_cog(SampleCog(bot))
