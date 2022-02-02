import discord
import slash_util

class SampleCog(slash_util.Cog):
    @slash_util.slash_command(guild_id=123)
    async def pog(self, ctx: slash_util.Context):
        await ctx.send("pog", ephemeral=True)

    @slash_util.message_command(guild_id=123)
    async def quote(self, ctx: slash_util.Context, message: discord.Message):  # the `message` parameter is REQURIED for message commands
        await ctx.send(f"> {message.clean_content}\n- {message.author}")

    @slash_util.user_command(guild_id=123)
    async def bonk(self, ctx: slash_util.Context, user: discord.Member):
        await ctx.send(f"{ctx.author} bonks {user} :hammer:")

def setup(bot):
    bot.add_cog(SampleCog(bot))
