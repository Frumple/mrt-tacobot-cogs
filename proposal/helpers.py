from datetime import datetime, timedelta
from discord import ForumChannel, ForumTag, Message, Thread
from enum import Enum
from functools import reduce
from redbot.core import Config, commands
from typing import Sequence

class DiscordTimestampFormatType(Enum):
  DEFAULT = None
  SHORT_TIME = 't'
  LONG_TIME = 'T'
  SHORT_DATE = 'd'
  LONG_DATE = 'D'
  SHORT_DATE_TIME = 'f'
  LONG_DATE_TIME = 'F'
  RELATIVE_TIME = 'R'

class ProposalState(Enum):
  NEW = 0
  APPROVED = 1
  REJECTED = 2
  EXTENDED = 3
  DEFERRED = 4

def datetime_to_discord_timestamp(date: datetime, format_type: DiscordTimestampFormatType = None) -> str:
  epoch = date.strftime('%s')
  format = f':{format_type.value}' if format_type.value is not None else ''
  return f'<t:{epoch}{format}>'

def get_forum_tag(tags: Sequence[ForumTag], tag_id: int) -> ForumTag:
  for tag in tags:
    if tag.id == tag_id:
      return tag
  return None

async def get_proposal_channel(cog: commands.Cog) -> ForumChannel:
  proposal_channel_id = await cog.config.proposal_channel_id()
  return await cog.bot.fetch_channel(proposal_channel_id)

async def get_proposal_channel_tag(cog: commands.Cog, tag_id: int) -> ForumTag:
  proposal_channel = await get_proposal_channel(cog)
  return get_forum_tag(proposal_channel.available_tags, tag_id)

async def get_thread_starter_message(thread: Thread) -> Message:
  if thread.starter_message is not None:
    return thread.starter_message

  async for message in thread.history(limit = 1, oldest_first = True):
    return message

def get_total_number_of_reactions(message: Message) -> int:
  reaction_counts = map(lambda reaction: reaction.count, message.reactions)
  return reduce(lambda a, b: a + b, reaction_counts, 0)

def get_voting_datetime(base_datetime: datetime, number_of_days: int) -> datetime:
  return round_datetime_to_current_hour(base_datetime + timedelta(days = number_of_days))

def round_datetime_to_current_hour(d: datetime) -> datetime:
  return d.replace(minute=0, second=0, microsecond=0)

async def set_proposal_state(config: Config, thread: Thread, state: ProposalState) -> None:
  proposal_channel_tags = thread.parent.available_tags

  approved_tag_id = await config.approved_tag_id()
  rejected_tag_id = await config.rejected_tag_id()
  extended_tag_id = await config.extended_tag_id()
  deferred_tag_id = await config.deferred_tag_id()

  approved_tag = get_forum_tag(proposal_channel_tags, approved_tag_id)
  rejected_tag = get_forum_tag(proposal_channel_tags, rejected_tag_id)
  extended_tag = get_forum_tag(proposal_channel_tags, extended_tag_id)
  deferred_tag = get_forum_tag(proposal_channel_tags, deferred_tag_id)

  await thread.remove_tags(approved_tag, rejected_tag, extended_tag, deferred_tag)

  match state:
    case ProposalState.APPROVED:
      await thread.add_tags(approved_tag)
    case ProposalState.REJECTED:
      await thread.add_tags(rejected_tag)
    case ProposalState.EXTENDED:
      await thread.add_tags(extended_tag)
    case ProposalState.DEFERRED:
      await thread.add_tags(deferred_tag)