from datetime import datetime, time, timedelta
from discord import Thread
from discord.ext import tasks
from redbot.core import Config
from redbot.core.bot import Red
from typing import List
from zoneinfo import ZoneInfo

from .helpers import DiscordTimestampFormatType, ProposalState, datetime_to_discord_timestamp, get_proposal_channel, get_thread_starter_message, set_proposal_state

def every_hour() -> List[datetime]:
  times = []
  for x in range(0, 23):
    times.append(time(hour = x))
  return times

class ProposalTasks:
  def __init__(self) -> None:
    self.bot: Red
    self.config: Config

  @tasks.loop(time = every_hour())
  async def check_for_expired_proposals(self) -> None:
    zone_info = ZoneInfo('UTC')
    now = datetime.now(zone_info)

    proposal_channel = await get_proposal_channel(self)

    initial_voting_days = await self.config.initial_voting_days()
    extended_voting_days = await self.config.extended_voting_days()

    approved_tag_id = await self.config.approved_tag_id()
    rejected_tag_id = await self.config.rejected_tag_id()
    extended_tag_id = await self.config.extended_tag_id()
    deferred_tag_id = await self.config.deferred_tag_id()

    # Iterate through all open and unlocked posts
    for thread in proposal_channel.threads:
      if not thread.locked:
        starter_message = await get_thread_starter_message(thread)

        extended_date = starter_message.created_at + timedelta(days = initial_voting_days)
        final_date = extended_date + timedelta(days = extended_voting_days)

        status_tag_ids = [approved_tag_id, rejected_tag_id, extended_tag_id, deferred_tag_id]

        # If the thread has no status tags and the initial voting period has passed,
        # add the extended tag to the thread and announce the extension.
        if not self.thread_has_tag_ids(thread, status_tag_ids):
          quorum = await self.config.quorum()
          final_timestamp = datetime_to_discord_timestamp(final_date, DiscordTimestampFormatType.LONG_DATE_TIME)

          if now >= extended_date:
            await set_proposal_state(self.config, thread, ProposalState.EXTENDED)
            await thread.send(f':hourglass: **This proposal has been automatically extended** by another {extended_voting_days} days to {final_timestamp} since it does not have the minimum {quorum} votes for quorum.')

        # Otherwise if the thread has already been extended and the extended voting period has passed,
        # add the deferred tag and announce that an admin will make a final decision on the proposal soon.
        elif self.thread_has_tag_ids(thread, [extended_tag_id]):
          if now >= final_date:
            await set_proposal_state(self.config, thread, ProposalState.DEFERRED)
            await thread.send(f':calendar: **This proposal has been automatically deferred** to the next GSM after reaching the end of the extended voting period. Please wait for an admin to review this proposal and finalize this deferral.')

  @check_for_expired_proposals.before_loop
  async def before_check_proposals(self) -> None:
    await self.bot.wait_until_ready()

  @staticmethod
  def thread_has_tag_ids(thread: Thread, tag_ids: List[int]) -> bool:
    for thread_tag in thread.applied_tags:
      if thread_tag.id in tag_ids:
        return True

    return False