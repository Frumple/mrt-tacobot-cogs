from redbot.core import Config, commands
from redbot.core.bot import Red

from .config import PasswordConfig

class Password(PasswordConfig, commands.Cog):
  """Allows users to obtain access passwords for external services."""

  def __init__(self, bot: Red):
    self.bot = bot

    default_config = {
      'services': {},
      'message_channel_id': None,
      'message_id': None,
      'message_text': '**Click these buttons to obtain passwords to external services:**',
      'log_channel_id': None,
      'response_lifespan': None
    }
    self.config = Config.get_conf(self, identifier = 908331620815439, force_registration = True)
    self.config.register_global(**default_config)
