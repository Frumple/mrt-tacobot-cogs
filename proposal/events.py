from datetime import datetime, timedelta
from discord import Message, Reaction, Thread, User

from functools import reduce
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.mod import is_mod_or_superior
from zoneinfo import ZoneInfo

from .helpers import DiscordTimestampFormatType, datetime_to_discord_timestamp

class ProposalEvents:
  def __init__(self):
    self.bot: Red
    self.config: Config

  @commands.Cog.listener()
  async def on_thread_create(self, thread: Thread) -> None:
    if not await self.is_thread_in_proposal_channel(thread):
      return

    initial_voting_days = await self.config.initial_voting_days()
    extended_voting_days = await self.config.extended_voting_days()
    quorum = await self.config.quorum()

    zone_info = ZoneInfo('UTC')
    extension_date = datetime.now(zone_info) + timedelta(days = initial_voting_days)
    extension_timestamp = datetime_to_discord_timestamp(extension_date, DiscordTimestampFormatType.LONG_DATE_TIME)

    # If the first message in a thread has not been posted yet (because of Discord being slow),
    # wait until it has been posted.
    if thread.last_message is None:
      await self.bot.wait_for('message', check = lambda message: message.channel == thread, timeout = 10)

    await thread.send('**This proposal is now open for voting to staff only.** Staff may vote using the following reactions:\n- :white_check_mark: - Approve the proposal\n- :x: - Reject the proposal\n- :hourglass: - Extend the proposal\n- :calendar: - Defer the proposal to the next GSM')
    await thread.send(f'If this proposal does not get the minimum {quorum} votes for quorum by {extension_timestamp} ({initial_voting_days} days from now), it will be automatically extended by another {extended_voting_days} days.')

  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    thread = message.channel

    if not await self.is_proposal_vote_reaction(reaction):
      return

    # If the user is not staff, remove the reaction and DM the user reminding them they cannot vote
    if not await is_mod_or_superior(self.bot, user):
      await reaction.remove(user)
      await user.send('Voting on proposals is restricted to staff only. Please do not add reactions to the first message of a proposal.')
      return

    # Otherwise, report the vote
    number_of_votes = self.get_total_number_of_reactions(message)
    quorum = await self.config.quorum()
    vote_count_string = self.get_vote_count_string(number_of_votes, quorum)

    match reaction.emoji:
      case self.UNICODE_WHITE_CHECK_MARK:
        await thread.send(f':white_check_mark: **{user.name}** has voted to **approve** this proposal. {vote_count_string}')
      case self.UNICODE_X:
        await thread.send(f':x: **{user.name}** has voted to **reject** this proposal. {vote_count_string}')
      case self.UNICODE_HOURGLASS:
        await thread.send(f':hourglass: **{user.name}** has voted to **extend** this proposal. {vote_count_string}')
      case self.UNICODE_CALENDAR:
        await thread.send(f':calendar: **{user.name}** has voted to **defer** this proposal to the next GSM. {vote_count_string}')

    # If the proposal has enough votes for quorum, announce it
    if number_of_votes == quorum:
      await thread.send(f':ballot_box: **This proposal now has the minimum {quorum} votes for quorum.** Please wait for an admin to review this proposal and decide on a final result.')

  @commands.Cog.listener()
  async def on_reaction_remove(self, reaction: Reaction, user: User) -> None:
    message = reaction.message
    thread = message.channel

    if not await self.is_proposal_vote_reaction(reaction):
      return

    # If the user is not staff, do nothing
    if not await is_mod_or_superior(self.bot, user):
      return

    # Otherwise, report the removal
    number_of_votes = self.get_total_number_of_reactions(message)
    quorum = await self.config.quorum()
    vote_count_string = self.get_vote_count_string(number_of_votes, quorum)

    match reaction.emoji:
      case self.UNICODE_WHITE_CHECK_MARK:
        await thread.send(f'**{user.name}** has rescinded their vote to **approve** this proposal. {vote_count_string}')
      case self.UNICODE_X:
        await thread.send(f'**{user.name}** has rescinded their vote to **reject** this proposal. {vote_count_string}')
      case self.UNICODE_HOURGLASS:
        await thread.send(f'**{user.name}** has rescinded their vote to **extend** this proposal. {vote_count_string}')
      case self.UNICODE_CALENDAR:
        await thread.send(f'**{user.name}** has rescinded their vote to **defer** this proposal to the next GSM. {vote_count_string}')

    # If the proposal has lost quorum, announce it
    if number_of_votes == quorum - 1:
      await thread.send(f'**This proposal no longer has the minimum {quorum} votes for quorum.**')

  # Return true if:
  # - Reaction is on a thread
  # - Reaction is on a thread in the configured channel
  # - Reaction is on the thread's starter message
  async def is_proposal_vote_reaction(self, reaction: Reaction) -> bool:
    message = reaction.message
    thread = message.channel

    return \
      isinstance(thread, Thread) and \
      await self.is_thread_in_proposal_channel(thread) and \
      message.id == thread.starter_message.id

  async def is_thread_in_proposal_channel(self, thread: Thread) -> bool:
    proposal_channel_id = await self.config.proposal_channel_id()
    return thread.parent_id == proposal_channel_id

  @staticmethod
  def get_total_number_of_reactions(message: Message) -> int:
    reaction_counts = map(lambda reaction: reaction.count, message.reactions)
    return reduce(lambda a, b: a + b, reaction_counts, 0)

  @staticmethod
  def get_vote_count_string(number_of_votes: int, quorum: int) -> str:
    return f'[{number_of_votes} / {quorum}]'