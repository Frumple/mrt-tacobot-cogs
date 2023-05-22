from discord import ForumChannel, Reaction, Thread, User
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red
from redbot.core.utils.mod import is_mod_or_superior

class Proposal(commands.Cog):
  """Facilitates staff-only voting in a Discord forum channel."""

  UNICODE_WHITE_CHECK_MARK = '\U00002705'
  UNICODE_X = '\U0000274C'
  UNICODE_HOURGLASS = '\U0000231B'
  UNICODE_CALENDAR = '\U0001F4C6'

  def __init__(self, bot: Red):
    self.bot = bot

    default_config = {
      'forum_channel': None
    }
    self.config = Config.get_conf(self, identifier=458426606406630, force_registration=True)
    self.config.register_global(**default_config)

  # Event handler when a user adds a reaction
  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    thread = message.channel

    if not await self.is_proposal_vote_reaction(reaction):
      return

    # If the reaction was made by a staff member, report the vote
    if await is_mod_or_superior(self.bot, user):
      match reaction.emoji:
        case self.UNICODE_WHITE_CHECK_MARK:
          await thread.send(f':white_check_mark: **{user.name}** has voted to **approve** this proposal.')
        case self.UNICODE_X:
          await thread.send(f':x: **{user.name}** has voted to **reject** this proposal.')
        case self.UNICODE_HOURGLASS:
          await thread.send(f':hourglass: **{user.name}** has voted to **extend** this proposal.')
        case self.UNICODE_CALENDAR:
          await thread.send(f':calendar: **{user.name}** has voted to **defer** this proposal to the next GSM.')

    # Otherwise, remove the reaction and DM the user reminding them they cannot vote
    else:
      await reaction.clear()
      await user.send('Voting on proposals is restricted to staff only. Please do not add reactions to the #proposals channel.')

  # Event handler when a user removes a reaction
  @commands.Cog.listener()
  async def on_reaction_remove(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    thread = message.channel

    if not await self.is_proposal_vote_reaction(reaction):
      return

    # If the reaction was made by a staff member, report the removal
    if await is_mod_or_superior(self.bot, user):
      match reaction.emoji:
        case self.UNICODE_WHITE_CHECK_MARK:
          await thread.send(f'**{user.name}** has rescinded their vote to **approve** this proposal.')
        case self.UNICODE_X:
          await thread.send(f'**{user.name}** has rescinded their vote to **reject** this proposal.')
        case self.UNICODE_HOURGLASS:
          await thread.send(f'**{user.name}** has rescinded their vote to **extend** this proposal.')
        case self.UNICODE_CALENDAR:
          await thread.send(f'**{user.name}** has rescinded their vote to **defer** this proposal to the next GSM.')

  # Return true if:
  # - Reaction is on a thread
  # - Reaction is on a thread in the configured channel
  # - Reaction is on the thread's starter message
  async def is_proposal_vote_reaction(self, reaction: Reaction) -> bool:
    message = reaction.message
    thread = message.channel

    forum_channel_id = await self.config.forum_channel()

    return \
      isinstance(thread, Thread) and \
      thread.parent_id == forum_channel_id and \
      message.id == thread.starter_message.id

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
    await self.config.forum_channel.set(channel.id)
    await ctx.send(f'Channel has been set to: {channel.mention}')
