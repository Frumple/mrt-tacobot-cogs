from discord import ForumChannel
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red

class ProposalConfig:
  def __init__(self):
    self.bot: Red
    self.config: Config

  @commands.hybrid_group(name='proposal_config')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config(self, ctx: commands.Context) -> None:
    """Configures proposal settings."""
    if ctx.invoked_subcommand is None:
      pass

  @proposal_config.command(name='channel')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_channel(self, ctx: commands.Context, channel: ForumChannel) -> None:
    """Sets the forum channel that will be monitored for proposals."""
    await self.config.proposal_channel.set(channel.id)
    await ctx.send(f'Channel has been set to: {channel.mention}')

  @proposal_config.command(name='quorum')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_quorum(self, ctx: commands.Context, quorum: commands.Range[int, 1]) -> None:
    """Sets the number of votes required for the proposal to reach quorum."""
    await self.config.quorum.set(quorum)
    await ctx.send(f'Quorum has been set to: {quorum}')
