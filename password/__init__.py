from .password import Password

async def setup(bot):
  await bot.add_cog(Password())