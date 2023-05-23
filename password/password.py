from discord import app_commands
from discord.errors import Forbidden
from redbot.core import Config, commands
from typing import Literal

from .config import PasswordConfig

# When adding or removing a service, these hard-coded choices must also be updated for the service to show up in slash commands.
# After changing this constant, restart the bot and run "[p]slash sync" to update the slash commands.
SERVICE_CHOICES = Literal['mumble', 'wiki', 'files', 'openttd']

class Password(PasswordConfig, commands.Cog):
  """Allows users to obtain access passwords for external services."""

  def __init__(self):
    default_config = {
      'services': {}
    }
    self.config = Config.get_conf(self, identifier=8373008182, force_registration=True)
    self.config.register_global(**default_config)

  @commands.hybrid_group(name="password")
  async def password(self, ctx: commands.Context) -> None:
    """Provides access passwords for external services."""
    if ctx.invoked_subcommand is None:
      pass

  @password.command(name="get")
  @app_commands.guild_only()
  @app_commands.describe(service_name = 'Name of the service')
  async def password_get(self, ctx, service_name: SERVICE_CHOICES) -> None:
    """Sends the password of a given service to the user via direct message."""
    async with self.config.services() as services:
      if service_name in services:
        await ctx.send(f'{ctx.author.mention} has requested the password for `{service_name}`.')
        try:
          service = services[service_name]
          description = service['description']
          password = service['password']
          await ctx.author.send(f'**{description}:** `{password}`')
        except Forbidden:
          await ctx.send('Error: Unable to send password via direct message.')
          await ctx.send('In your Privacy Settings for this Discord server, please make sure to "Allow direct messages from server members", and then try requesting the password again.')
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')

  @password.command(name="list")
  @app_commands.guild_only()
  async def password_list(self, ctx) -> None:
    """Lists all services."""
    async with self.config.services() as services:
      service_names = [*services]
      output = '\n'.join(map(lambda name: f'- `{name}`', service_names))
      await ctx.send(f'All services:\n{output}')
