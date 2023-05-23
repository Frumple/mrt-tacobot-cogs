from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify

class DynmapConfig:
  def __init__(self):
    self.bot: Red
    self.config: Config

  @commands.hybrid_group(name='dynmap_config')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config(self, ctx: commands.Context) -> None:
    """Configures Dynmap settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config.command(name='get_all')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_get_all(self, ctx: commands.Context) -> None:
    """Displays all settings."""
    async with self.config.all() as settings:
      output = '{:<40} | {:<40}\n'.format('Key', 'Value')
      for key, value in settings.items():
        if value is None:
          value = 'None'
        elif key in ['pterodactyl_api_key', 'pterodactyl_server_id']:
          value = '<redacted>'

        if isinstance(value, str) or isinstance(value, int) or value is None:
          output += '{:<40} | {:<40}\n'.format(key, value)
      for page in pagify(output):
        await ctx.send(f'```{page}```')

  @dynmap_config.command(name='pterodactyl_host')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_pterodactyl_host(self, ctx: commands.Context, host: str) -> None:
    """Sets the Pterodactyl API host URL."""
    await self.config.pterodactyl_api_host.set(host)
    await ctx.send(f'Pterodactyl API host URL has been set to `{host}`.')

  @dynmap_config.command(name='pterodactyl_key')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_pterodactyl_key(self, ctx: commands.Context, key: str) -> None:
    """Sets the Pterodactyl API client key."""
    await self.config.pterodactyl_api_key.set(key)
    await ctx.send('Pterodactyl API client key has been set.')

  @dynmap_config.command(name='pterodactyl_id')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_pterodactyl_id(self, ctx: commands.Context, id: str) -> None:
    """Sets the Pterodactyl API server ID."""
    await self.config.pterodactyl_server_id.set(id)
    await ctx.send(f'Pterodactyl API server ID has been set.')

  @dynmap_config.command(name='render_world')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_render_world(self, ctx: commands.Context, world: str) -> None:
    """Sets the Minecraft world to render."""
    await self.config.render_world.set(world)
    await ctx.send(f'Render world set to `{world}`.')

  @dynmap_config.command(name='render_dimension')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_render_dimension(self, ctx: commands.Context, dimension: str) -> None:
    """Sets the Minecraft dimension to render."""
    await self.config.render_dimension.set(dimension)
    await ctx.send(f'Render dimension set to `{dimension}`.')

  @dynmap_config.command(name='render_default_radius')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_render_default_radius(self, ctx: commands.Context, radius: int) -> None:
    """Sets the default render radius (when radius is not specified in the render command)."""
    await self.config.render_default_radius.set(radius)
    await ctx.send(f'Default render radius set to `{radius}`.')

  @dynmap_config.command(name='render_queue_size')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_render_queue_size(self, ctx: commands.Context, size: int) -> None:
    """Sets the maximum number of renders that can be queued, including the currently running render."""
    await self.config.render_queue_size.set(size)
    await ctx.send(f'Render queue size set to `{size}`.')

  @dynmap_config.command(name='web_host')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_web_host(self, ctx: commands.Context, host: str) -> None:
    """Sets the Dynmap host URL used in the embed link."""
    await self.config.web_host.set(host)
    await ctx.send(f'Dynmap host URL set to `{host}`.')

  @dynmap_config.command(name='web_map')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_web_map(self, ctx: commands.Context, map: str) -> None:
    """Sets the Dynmap map name used in the embed link."""
    await self.config.web_map.set(map)
    await ctx.send(f'Dynmap map name set to `{map}`.')

  @dynmap_config.command(name='web_zoom')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_web_zoom(self, ctx: commands.Context, zoom: int) -> None:
    """Sets the Dynmap zoom level used in the embed link."""
    await self.config.web_zoom.set(zoom)
    await ctx.send(f'Dynmap zoom level set to `{zoom}`.')

  @dynmap_config.command(name='web_y')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_web_y(self, ctx: commands.Context, y: int) -> None:
    """Sets the Dynmap Y coordinate used in the embed link."""
    await self.config.web_y.set(y)
    await ctx.send(f'Dynmap Y coordinate set to `{y}`.')

  @dynmap_config.command(name='queued_render_start_delay')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_delay_queued_render_start(self, ctx: commands.Context, delay: int) -> None:
    """Sets the number of seconds for a queued render to wait after the current render has finished."""
    await self.config.queue_render_delay_in_seconds.set(delay)
    await ctx.send(f'Queued render delay set to `{delay}` seconds.')

  @dynmap_config.command(name='elapsed_interval')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_interval_elapsed(self, ctx: commands.Context, interval: int) -> None:
    """While a render is in progress, update the elapsed time every X seconds."""
    await self.config.elapsed_time_interval_in_seconds.set(interval)
    await ctx.send(f'Elapsed time interval set to `{interval}` seconds.')

  @dynmap_config.command(name='cancel_interval')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_interval_cancel(self, ctx: commands.Context, interval: int) -> None:
    """While a render is in progress, check if a cancellation has been requested every X seconds."""
    await self.config.cancellation_check_interval_in_seconds.set(interval)
    await ctx.send(f'Cancellation check time interval set to `{interval}` seconds.')

  @dynmap_config.command(name='auth_timeout')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_timeout_auth(self, ctx: commands.Context, timeout: int) -> None:
    """Sets number of seconds to wait for a successful response after sending a websocket auth request."""
    await self.config.auth_timeout_in_seconds.set(timeout)
    await ctx.send(f'Auth timeout set to `{timeout}` seconds.')

  @dynmap_config.command(name='command_timeout')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_timeout_command(self, ctx: commands.Context, timeout: int) -> None:
    """Sets number of seconds to wait for a console response after starting or cancelling a Dynmap render."""
    await self.config.command_timeout_in_seconds.set(timeout)
    await ctx.send(f'Command timeout set to `{timeout}` seconds.')

  @dynmap_config.command(name='render_timeout')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_config_timeout_render(self, ctx: commands.Context, timeout: int) -> None:
    """Sets number of seconds to wait for a console message indicating that a Dynmap render has finished."""
    await self.config.render_timeout_in_seconds.set(timeout)
    await ctx.send(f'Render timeout set to `{timeout}` seconds.')

  @dynmap_config.command(name='clear_queue')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def dynmap_clear_queue(self, ctx: commands.Context) -> None:
    """Clears the queue of current Dynmap renders. Caution: all current renders will likely fail."""
    await self.config.render_queue.clear()
    await ctx.send('Render queue cleared.')