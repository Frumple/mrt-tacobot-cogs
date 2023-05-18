from .dynmap import Dynmap

async def setup(bot):
  await bot.add_cog(Dynmap(bot))