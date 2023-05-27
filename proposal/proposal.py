from datetime import timedelta
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red

from .config import ProposalConfig
from .events import ProposalEvents
from .tasks import ProposalTasks
from .helpers import DiscordTimestampFormatType, ProposalState, datetime_to_discord_timestamp, set_proposal_state

class Proposal(ProposalConfig, ProposalEvents, ProposalTasks, commands.Cog):
  """Facilitates staff-only voting in a Discord forum channel."""

  UNICODE_WHITE_CHECK_MARK = '\U00002705'
  UNICODE_X = '\U0000274C'
  UNICODE_HOURGLASS = '\U0000231B'
  UNICODE_CALENDAR = '\U0001F4C6'

  def __init__(self, bot: Red):
    self.bot = bot

    default_config = {
      'proposal_channel_id': None,
      'initial_voting_days': 7,
      'extended_voting_days': 7,
      'quorum': 1,
      'approved_tag_id': None,
      'rejected_tag_id': None,
      'extended_tag_id': None,
      'deferred_tag_id': None
    }
    self.config = Config.get_conf(self, identifier = 458426606406630, force_registration = True)
    self.config.register_global(**default_config)

    self.check_for_expired_proposals.start()

  def cog_unload(self):
    self.check_for_expired_proposals.cancel()

  @commands.hybrid_group(name='proposal')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal(self, ctx: commands.Context) -> None:
    """Manages proposals."""
    if ctx.invoked_subcommand is None:
      pass

  @proposal.command(name='approve')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_approve(self, ctx: commands.Context) -> None:
    """Approves the proposal thread where this command is run."""
    if not await self.is_thread_in_proposal_channel(ctx.channel):
      await ctx.send('This command can only be run in threads of the proposal channel.')
      return

    await set_proposal_state(self.config, ctx.channel, ProposalState.APPROVED)
    await ctx.send(f':white_check_mark: {ctx.channel.owner.mention} **This proposal has been approved.**')
    await self.report_votes(ctx)
    await ctx.channel.edit(archived = True, locked = True)

  @proposal.command(name='reject')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_reject(self, ctx: commands.Context) -> None:
    """Rejects the proposal thread where this command is run."""
    if not await self.is_thread_in_proposal_channel(ctx.channel):
      await ctx.send('This command can only be run in threads of the proposal channel.')
      return

    await set_proposal_state(self.config, ctx.channel, ProposalState.REJECTED)
    await ctx.send(f':x: {ctx.channel.owner.mention} **This proposal has been rejected.**')
    await self.report_votes(ctx)
    await ctx.channel.edit(archived = True, locked = True)

  @proposal.command(name='extend')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_extend(self, ctx: commands.Context) -> None:
    """Extends the proposal thread where this command is run."""
    if not await self.is_thread_in_proposal_channel(ctx.channel):
      await ctx.send('This command can only be run in threads of the proposal channel.')
      return

    initial_voting_days = await self.config.initial_voting_days()
    extended_voting_days = await self.config.extended_voting_days()

    final_date = ctx.channel.starter_message.created_at + timedelta(days = initial_voting_days) + timedelta(days = extended_voting_days)
    final_timestamp = datetime_to_discord_timestamp(final_date, DiscordTimestampFormatType.LONG_DATE_TIME)

    await set_proposal_state(self.config, ctx.channel, ProposalState.EXTENDED)
    await ctx.send(f':hourglass: **This proposal has been extended until {final_timestamp}.**')
    await self.report_votes(ctx)
    await ctx.channel.edit(archived = True, locked = True)

  @proposal.command(name='defer')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def proposal_defer(self, ctx: commands.Context) -> None:
    """Defers the proposal thread where this command is run."""
    if not await self.is_thread_in_proposal_channel(ctx.channel):
      await ctx.send('This command can only be run in threads of the proposal channel.')
      return

    await set_proposal_state(self.config, ctx.channel, ProposalState.DEFERRED)
    await ctx.send(f':hourglass: **This proposal has been deferred to the next GSM.**')
    await self.report_votes(ctx)

  async def report_votes(self, ctx: commands.Context) -> None:
    reactions = ctx.channel.starter_message.reactions
    text = '**Vote Summary:**\n\n'

    for reaction in reactions:
      header = None

      match reaction.emoji:
        case self.UNICODE_WHITE_CHECK_MARK:
          header = f':white_check_mark: **Approve ({reaction.count})**'
        case self.UNICODE_X:
          header = f':x: **Reject ({reaction.count})**'
        case self.UNICODE_HOURGLASS:
          header = f':hourglass: **Extend ({reaction.count})**'
        case self.UNICODE_CALENDAR:
          header = f':calendar: **Defer ({reaction.count})**'

      if header is not None:
        users = [user async for user in reaction.users()]
        user_names = map(lambda u: f'- {u.display_name}', users)
        user_text = "\n".join(user_names)

        text += f'{header}\n{user_text}\n\n'

    await ctx.send(text)
