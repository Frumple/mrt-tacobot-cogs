from discord import app_commands
from discord.errors import Forbidden
from redbot.core import Config, commands, checks
from typing import Literal

# When adding or removing a service, these hard-coded choices must also be updated for the service to show up in slash commands.
# After changing this constant, restart the bot and run "[p]slash sync" to update the slash commands.
SERVICE_CHOICES = Literal['mumble', 'wiki', 'files', 'openttd']

class Password(commands.Cog):
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

  @commands.hybrid_group(name="password_config")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config(self, ctx: commands.Context) -> None:
    """Configures password settings."""
    if ctx.invoked_subcommand is None:
      pass

  @password_config.command(name="add_service")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_add_service(self, ctx, service_name: str, *, service_description: str) -> None:
    """Adds a new service."""
    async with self.config.services() as services:
      if service_name not in services:
        services[service_name] = {
          'description': service_description,
          'password': ""
        }
        await ctx.send(f'Service `{service_name}` added. Set the password with `{ctx.prefix}password_config set_password {service_name}`.')
        await ctx.send('You will also need to add this service directly to password.py in order to update slash commands.')
      else:
        await ctx.send(f'Service `{service_name}` already exists.')

  @password_config.command(name="remove_service")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_remove_service(self, ctx, service_name: str) -> None:
    """Removes an existing service."""
    async with self.config.services() as services:
      if service_name in services:
        del services[service_name]
        await ctx.send(f'Service `{service_name}` removed.')
        await ctx.send('You will also need to remove this service directly from password.py in order to update slash commands.')
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')

  @password_config.command(name="set_password")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_set_password(self, ctx, service_name: str, password: str) -> None:
    """Set the password for the given service."""
    async with self.config.services() as services:
      if service_name in services:
        services[service_name] = {
          'description': services[service_name]['description'],
          'password': password
        }
        await ctx.send(f'Password set for service `{service_name}`.')
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')

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
