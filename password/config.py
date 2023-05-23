from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red

class PasswordConfig:
  def __init__(self):
    self.bot: Red
    self.config: Config

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
        await ctx.send('You will also need to add this service directly to password.py in order to update slash commands choices.')
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
        await ctx.send('You will also need to remove this service directly from password.py in order to update slash commands choices.')
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
