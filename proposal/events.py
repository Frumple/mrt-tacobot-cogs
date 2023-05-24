from discord import Message, Reaction, Thread, User
from functools import reduce
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.mod import is_mod_or_superior

class ProposalEvents:
  def __init__(self):
    self.bot: Red
    self.config: Config

  # Event handler when a user adds a reaction
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

  # Event handler when a user removes a reaction
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

    forum_channel_id = await self.config.proposal_channel()

    return \
      isinstance(thread, Thread) and \
      thread.parent_id == forum_channel_id and \
      message.id == thread.starter_message.id

  @staticmethod
  def get_total_number_of_reactions(message: Message) -> int:
    reaction_counts = map(lambda reaction: reaction.count, message.reactions)
    return reduce(lambda a, b: a + b, reaction_counts, 0)

  @staticmethod
  def get_vote_count_string(number_of_votes: int, quorum: int) -> str:
    return f'`[{number_of_votes} / {quorum} votes for quorum]`'