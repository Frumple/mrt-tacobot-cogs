from datetime import datetime, time, timedelta
from discord.ext import tasks
from redbot.core import Config
from redbot.core.bot import Red
from typing import List
from zoneinfo import ZoneInfo

from .helpers import DiscordTimestampFormatType, datetime_to_discord_timestamp, get_forum_tag, thread_has_tag_ids

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

    print(f'Checking for expired proposals at: {now}', flush = True)

    proposal_channel_id = await self.config.proposal_channel_id()
    if proposal_channel_id is None:
      print('Proposal channel is not defined.', flush = True)
      return

    proposal_channel = await self.bot.fetch_channel(proposal_channel_id)

    approved_tag_id = await self.config.approved_tag_id()
    if approved_tag_id is None:
      print('Approved tag is not defined.', flush = True)
      return

    rejected_tag_id = await self.config.rejected_tag_id()
    if rejected_tag_id is None:
      print('Rejected tag is not defined.', flush = True)
      return

    extended_tag_id = await self.config.extended_tag_id()
    if extended_tag_id is None:
      print('Extended tag is not defined.', flush = True)
      return

    deferred_tag_id = await self.config.deferred_tag_id()
    if deferred_tag_id is None:
      print('Deferred tag is not defined.', flush = True)
      return

    extended_tag = get_forum_tag(proposal_channel.available_tags, extended_tag_id)
    if extended_tag is None:
      print('Extended tag does not exist.')
      return

    deferred_tag = get_forum_tag(proposal_channel.available_tags, deferred_tag_id)
    if deferred_tag is None:
      print('Deferred tag does not exist.')
      return

    # Iterate through all open and unlocked posts
    for thread in proposal_channel.threads:
      if not thread.locked:
        print(thread.name, flush = True)

        status_tag_ids = [approved_tag_id, rejected_tag_id, extended_tag_id, deferred_tag_id]

        # If the thread has no status tags and the initial voting period has passed,
        # add the extended tag to the thread and announce the extension.
        if not thread_has_tag_ids(thread, status_tag_ids):
          initial_voting_days = await self.config.initial_voting_days()
          extended_voting_days = await self.config.extended_voting_days()
          quorum = await self.config.quorum()

          zone_info = ZoneInfo('UTC')
          final_date = datetime.now(zone_info) + timedelta(days = extended_voting_days)
          final_timestamp = datetime_to_discord_timestamp(final_date, DiscordTimestampFormatType.LONG_DATE_TIME)

          if now >= thread.starter_message.created_at + timedelta(days = initial_voting_days):
            await thread.add_tags(extended_tag)
            await thread.send(f':hourglass: **This proposal has been automatically extended** by another {extended_voting_days} days to {final_timestamp} since it does not have the minimum {quorum} votes for quorum.')

        # Otherwise if the thread has already been extended and the extended voting period has passed,
        # add the deferred tag and announce that an admin will make a final decision on the proposal soon.
        elif thread_has_tag_ids(thread, [extended_tag_id]):
          if now >= thread.starter_message.created_at + timedelta(days = initial_voting_days) + timedelta(days = extended_voting_days):
            await thread.remove_tags(extended_tag)
            await thread.add_tags(deferred_tag)
            await thread.send(f':calendar: **This proposal has been automatically deferred** to the next GSM after reaching the end of the extended voting period. Please wait for an admin to review this proposal and finalize this deferral.')

  @check_for_expired_proposals.before_loop
  async def before_check_proposals(self) -> None:
    await self.bot.wait_until_ready()
