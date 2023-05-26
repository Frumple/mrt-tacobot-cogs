from redbot.core import Config, commands
from redbot.core.bot import Red

from .config import ProposalConfig
from .events import ProposalEvents
from .tasks import ProposalTasks

class Proposal(ProposalConfig, ProposalEvents, ProposalTasks, commands.Cog):
  """Facilitates staff-only voting in a Discord forum channel."""

  UNICODE_WHITE_CHECK_MARK = '\U00002705'
  UNICODE_X = '\U0000274C'
  UNICODE_HOURGLASS = '\U0000231B'
  UNICODE_CALENDAR = '\U0001F4C6'

  def __init__(self, bot: Red):
    self.bot = bot

    default_config = {
      'proposal_channel_id': None,
      'initial_voting_days': 7,
      'extended_voting_days': 7,
      'quorum': 1,
      'approved_tag_id': None,
      'rejected_tag_id': None,
      'extended_tag_id': None,
      'deferred_tag_id': None
    }
    self.config = Config.get_conf(self, identifier = 458426606406630, force_registration = True)
    self.config.register_global(**default_config)

    self.check_for_expired_proposals.start()

  def cog_unload(self):
    self.check_for_expired_proposals.cancel()