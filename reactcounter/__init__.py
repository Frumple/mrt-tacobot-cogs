from .reactcounter import ReactCounter

async def setup(bot):
  await bot.add_cog(ReactCounter(bot))