from datetime import datetime
from discord import ForumTag, Thread
from enum import Enum
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

def datetime_to_discord_timestamp(date: datetime, format_type: DiscordTimestampFormatType = None) -> str:
  epoch = date.strftime('%s')
  format = f':{format_type.value}' if format_type.value is not None else ''
  return f'<t:{epoch}{format}>'

def get_forum_tag(tags: Sequence[ForumTag], tag_id: int) -> ForumTag:
  for tag in tags:
    if tag.id == tag_id:
      return tag
  return None

def thread_has_tag_ids(thread: Thread, tag_ids: Sequence[int]) -> bool:
  for thread_tag in thread.applied_tags:
    if thread_tag.id in tag_ids:
      return True

  return False