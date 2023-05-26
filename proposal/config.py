from discord import ForumChannel, ForumTag, NotFound
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red

from .helpers import get_forum_tag

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
    await self.config.proposal_channel_id.set(channel.id)
    await ctx.send(f'Channel has been set to: {channel.mention}')

  @proposal_config.command(name='initial_voting_days')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_initial_voting_days(self, ctx: commands.Context, days: commands.Range[int, 1]) -> None:
    """Sets the number of days before the proposal is extended."""
    await self.config.initial_voting_days.set(days)
    await ctx.send(f'Initial voting period in days has been set to: {days}')

  @proposal_config.command(name='extended_voting_days')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_extended_voting_days(self, ctx: commands.Context, days: commands.Range[int, 1]) -> None:
    """Sets the number of days after a proposal is extended."""
    await self.config.extended_voting_days.set(days)
    await ctx.send(f'Extended voting period in days has been set to: {days}')

  @proposal_config.command(name='quorum')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_quorum(self, ctx: commands.Context, quorum: commands.Range[int, 1]) -> None:
    """Sets the number of votes required for the proposal to reach quorum."""
    await self.config.quorum.set(quorum)
    await ctx.send(f'Quorum has been set to: {quorum}')

  @proposal_config.command(name='approved_tag')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_approved_tag(self, ctx: commands.Context, tag_id: int) -> None:
    """Sets the forum tag that indicates a proposal has been approved."""
    tag = self.get_proposal_channel_tag(tag_id)
    await self.config.approved_tag_id.set(tag_id)
    await ctx.send(f'Approved tag has been set to: {tag.emoji} {tag.name}')

  @proposal_config.command(name='rejected_tag')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_rejected_tag(self, ctx: commands.Context, tag_id: int) -> None:
    """Sets the forum tag that indicates a proposal has been rejected."""
    tag = self.get_proposal_channel_tag(tag_id)
    await self.config.rejected_tag_id.set(tag_id)
    await ctx.send(f'Rejected tag has been set to: {tag.emoji} {tag.name}')

  @proposal_config.command(name='extended_tag')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_extended_tag(self, ctx: commands.Context, tag_id: int) -> None:
    """Sets the forum tag that indicates a proposal has been extended."""
    tag = self.get_proposal_channel_tag(tag_id)
    await self.config.extended_tag_id.set(tag_id)
    await ctx.send(f'Extended tag has been set to: {tag.emoji} {tag.name}')

  @proposal_config.command(name='deferred_tag')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_deferred_tag(self, ctx: commands.Context, tag_id: int) -> None:
    """Sets the forum tag that indicates a proposal has been deferred."""
    tag = self.get_proposal_channel_tag(tag_id)
    await self.config.deferred_tag_id.set(tag_id)
    await ctx.send(f'Deferred tag has been set to: {tag.emoji} {tag.name}')

  @proposal_config.command(name='list_tags')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_config_list_all_tags(self, ctx: commands.Context) -> None:
    """Lists all forum tags and IDs from the proposal channel."""
    proposal_channel = await self.get_proposal_channel()
    for tag in proposal_channel.available_tags:
      await ctx.send(f'Tag Name: `{tag.name}`, ID: `{tag.id}`, Emoji: {tag.emoji}')

  async def get_proposal_channel(self) -> ForumChannel:
    proposal_channel_id = await self.config.proposal_channel_id()
    return await self.bot.fetch_channel(proposal_channel_id)

  async def get_proposal_channel_tag(self, tag_id: int) -> ForumTag:
    proposal_channel = await self.get_proposal_channel()
    return get_forum_tag(proposal_channel.available_tags, tag_id)
