from discord import RawReactionActionEvent, Reaction, Thread, User
from redbot.core import commands, checks
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

  # Event handler when a user adds a reaction
  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    channel = message.channel

    if not self.is_proposal_vote_reaction(reaction):
      return

    # If the reaction was made by a staff member, report the vote
    if await is_mod_or_superior(self.bot, user):
      match reaction.emoji:
        case self.UNICODE_WHITE_CHECK_MARK:
          await channel.send(f':white_check_mark: **{user.name}** has voted to **approve** this proposal.')
        case self.UNICODE_X:
          await channel.send(f':x: **{user.name}** has voted to **reject** this proposal.')
        case self.UNICODE_HOURGLASS:
          await channel.send(f':hourglass: **{user.name}** has voted to **extend** this proposal.')
        case self.UNICODE_CALENDAR:
          await channel.send(f':calendar: **{user.name}** has voted to **defer** this proposal to the next GSM.')

    # Otherwise, remove the reaction and DM the user reminding them they cannot vote
    else:
      await reaction.clear()
      await user.send('Voting on proposals is restricted to staff only. Please do not add reactions to the #proposals channel.')

  # Event handler when a user removes a reaction
  @commands.Cog.listener()
  async def on_reaction_remove(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    channel = message.channel

    if not self.is_proposal_vote_reaction(reaction):
      return

    # If the reaction was made by a staff member, report the removal
    if await is_mod_or_superior(self.bot, user):
      match reaction.emoji:
        case self.UNICODE_WHITE_CHECK_MARK:
          await channel.send(f'**{user.name}** has rescinded their vote to **approve** this proposal.')
        case self.UNICODE_X:
          await channel.send(f'**{user.name}** has rescinded their vote to **reject** this proposal.')
        case self.UNICODE_HOURGLASS:
          await channel.send(f'**{user.name}** has rescinded their vote to **extend** this proposal.')
        case self.UNICODE_CALENDAR:
          await channel.send(f'**{user.name}** has rescinded their vote to **defer** this proposal to the next GSM.')

  # Return true if:
  # - Reaction is on a thread
  # - Reaction is on a thread in the specified channel
  # - Reaction is on the thread's starter message
  def is_proposal_vote_reaction(self, reaction: Reaction) -> bool:
    message = reaction.message
    channel = message.channel

    # TODO: Use channel id from config instead

    return \
      isinstance(channel, Thread) and \
      channel.parent_id == 1109599772685377606 and \
      message.id == channel.starter_message.id
