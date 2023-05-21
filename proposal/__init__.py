from .proposal import Proposal

async def setup(bot):
  await bot.add_cog(Proposal(bot))