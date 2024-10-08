from datetime import datetime, time, timedelta
from discord import Thread
from discord.ext import tasks
from redbot.core import Config
from redbot.core.bot import Red
from typing import List
from zoneinfo import ZoneInfo

from .helpers import DiscordTimestampFormatType, ProposalState, datetime_to_discord_timestamp, get_proposal_channel, get_thread_starter_message, get_total_number_of_reactions, get_voting_datetime, set_proposal_state

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
  async def check_proposals(self) -> None:
    now = datetime.now(ZoneInfo('UTC'))

    proposal_channel = await get_proposal_channel(self)

    quorum = await self.config.quorum()

    minimum_voting_days = await self.config.minimum_voting_days()
    standard_voting_days = await self.config.standard_voting_days()
    extended_voting_days = await self.config.extended_voting_days()

    approved_tag_id = await self.config.approved_tag_id()
    rejected_tag_id = await self.config.rejected_tag_id()
    extended_tag_id = await self.config.extended_tag_id()
    deferred_tag_id = await self.config.deferred_tag_id()

    # Iterate through all open and unlocked posts
    for thread in proposal_channel.threads:
      if not thread.locked:
        starter_message = await get_thread_starter_message(thread)

        minimum_date = get_voting_datetime(starter_message.created_at, minimum_voting_days)
        extended_date = get_voting_datetime(starter_message.created_at, standard_voting_days)
        final_date = get_voting_datetime(starter_message.created_at, extended_voting_days)

        status_tag_ids = [approved_tag_id, rejected_tag_id, extended_tag_id, deferred_tag_id]

        # TODO: Use a "New" tag to indicate a proposal that hasn't reached the minimum voting period yet.

        # If the thread has reached the minimum voting period,
        # post a message indicating that the proposal can now be resolved if it has reached quorum.
        if minimum_date - timedelta(minutes = 1) < now < minimum_date + timedelta(minutes = 1):
          number_of_votes = get_total_number_of_reactions(starter_message)
          if number_of_votes >= quorum:
            await thread.send(f'**This proposal has reached the minimum voting period of {minimum_voting_days} days.** Please wait for an admin to review this proposal and decide on a final result.')
          else:
            await thread.send(f'**This proposal has reached the minimum voting period of {minimum_voting_days} days.** However, it has not reached quorum yet and needs {quorum - number_of_votes} more votes.')

        # If the thread has no status tags and the standard voting period has passed,
        # add the extended tag to the thread and announce the extension.
        if not self.thread_has_tag_ids(thread, status_tag_ids):
          quorum = await self.config.quorum()
          final_timestamp = datetime_to_discord_timestamp(final_date, DiscordTimestampFormatType.LONG_DATE_TIME)

          if now >= extended_date:
            await set_proposal_state(self.config, thread, ProposalState.EXTENDED)
            await thread.send(f':hourglass: **This proposal has been automatically extended** by another {extended_voting_days - standard_voting_days} days to {final_timestamp} since it does not have the minimum {quorum} votes for quorum.')

            notification_channel_id = await self.config.notification_channel_id()
            if notification_channel_id is not None:
              notification_channel = await self.bot.fetch_channel(notification_channel_id)
              await notification_channel.send(f':hourglass: **A proposal has been automatically extended after {standard_voting_days} days. Please review and vote:** {thread.mention}')

        # Otherwise if the thread has already been extended and the extended voting period has passed,
        # add the deferred tag and announce that an admin will make a final decision on the proposal soon.
        elif self.thread_has_tag_ids(thread, [extended_tag_id]):
          if now >= final_date:
            await set_proposal_state(self.config, thread, ProposalState.DEFERRED)
            await thread.send(f':calendar: **This proposal has been automatically deferred** to the next GSM after reaching the end of the extended voting period. Please wait for an admin to review this proposal and finalize this deferral.')

            notification_channel_id = await self.config.notification_channel_id()
            if notification_channel_id is not None:
              notification_channel = await self.bot.fetch_channel(notification_channel_id)
              await notification_channel.send(f':calendar: **A proposal has been automatically deferred after {extended_voting_days} days. Please wait for an admin to review:** {thread.mention}')

  @check_proposals.before_loop
  async def before_check_proposals(self) -> None:
    await self.bot.wait_until_ready()

  @staticmethod
  def thread_has_tag_ids(thread: Thread, tag_ids: List[int]) -> bool:
    for thread_tag in thread.applied_tags:
      if thread_tag.id in tag_ids:
        return True

    return False