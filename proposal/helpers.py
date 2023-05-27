from datetime import datetime
from discord import ForumTag, Thread
from enum import Enum
from redbot.core import Config
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

def thread_has_tag_ids(thread: Thread, tag_ids: Sequence[int]) -> bool:
  for thread_tag in thread.applied_tags:
    if thread_tag.id in tag_ids:
      return True

  return False