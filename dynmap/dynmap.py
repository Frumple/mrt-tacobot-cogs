from aiohttp import ClientSession, ClientWebSocketResponse
from asyncio import TimeoutError, wait_for
from discord import Color, Embed
from enum import Enum
from functools import reduce
from http.client import HTTPException
from redbot.core import Config, commands, checks
from timeit import default_timer as timer
from urllib.parse import urljoin

class ConsoleResponseResult(Enum):
  SUCCESS = 1
  FAILURE = 2
  TIMEOUT = 3

class DynmapError(Exception):
  pass

class Dynmap(commands.Cog):
  """Allows users to run dynmap radius renders from Discord."""

  UNICODE_WHITE_CHECK_MARK = '\U00002705'
  UNICODE_X = '\U0000274C'

  def __init__(self):
    default_guild = {
      'pterodactyl_api_host': None,
      'pterodactyl_api_key': None,
      'pterodactyl_server_id': None,
      'render_world': 'new',
      'render_default_radius': 300,
      'render_min_radius': 100,
      'render_max_radius': 300,
      'render_max_dimension': 30000,
      'web_host': None,
      'web_map': 'flat',
      'web_zoom': 6,
      'web_y': 64,
      'start_timeout_in_seconds': 10,
      'end_timeout_in_seconds': 600
    }
    self.config = Config.get_conf(self, identifier=8373008182, force_registration=True)
    self.config.register_guild(**default_guild)

  @commands.group()
  async def dynmap(self, ctx: commands.Context):
    if ctx.invoked_subcommand is None:
      pass

  @dynmap.group(name='config')
  @checks.admin_or_permissions()
  async def dynmap_config(self, ctx):
    """Configures settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config.group(name='pterodactyl')
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl(self, ctx):
    """Configures Pterodactyl connection settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_pterodactyl.command(name="host")
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_host(self, ctx, host: str):
    """Sets the Pterodactyl API host URL."""
    await self.config.guild(ctx.guild).pterodactyl_api_host.set(host)
    await ctx.send(f'Pterodactyl API host URL has been set to `{host}`.')

  @dynmap_config_pterodactyl.command(name="key")
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_key(self, ctx, key: str):
    """Sets the Pterodactyl API client key."""
    await self.config.guild(ctx.guild).pterodactyl_api_key.set(key)
    await ctx.send('Pterodactyl API client key has been set.')

  @dynmap_config_pterodactyl.command(name="id")
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_id(self, ctx, id: str):
    """Sets the Pterodactyl server ID."""
    await self.config.guild(ctx.guild).pterodactyl_server_id.set(id)
    await ctx.send(f'Pterodactyl API server ID has been set to `{id}`.')

  @dynmap_config.group(name='render')
  @checks.admin_or_permissions()
  async def dynmap_config_render(self, ctx):
    """Configures dynmap render settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_render.command(name="world")
  @checks.admin_or_permissions()
  async def dynmap_config_render_world(self, ctx, world: str):
    """Sets the world to render."""
    await self.config.guild(ctx.guild).render_world.set(world)
    await ctx.send(f'Render world set to `{world}`.')

  @dynmap_config_render.command(name="default_radius")
  @checks.admin_or_permissions()
  async def dynmap_config_render_default_radius(self, ctx, radius: int):
    """Sets the default render radius (when radius is not specified in the render command)."""
    await self.config.guild(ctx.guild).render_min_radius.set(radius)
    await ctx.send(f'Default render radius set to `{radius}`.')

  @dynmap_config_render.command(name="min_radius")
  @checks.admin_or_permissions()
  async def dynmap_config_render_min_radius(self, ctx, radius: int):
    """Sets the minimum render radius."""
    await self.config.guild(ctx.guild).render_min_radius.set(radius)
    await ctx.send(f'Minimum render radius set to `{radius}`.')

  @dynmap_config_render.command(name="max_radius")
  @checks.admin_or_permissions()
  async def dynmap_config_render_max_radius(self, ctx, radius: int):
    """Sets the maximum render radius."""
    await self.config.guild(ctx.guild).render_max_radius.set(radius)
    await ctx.send(f'Maximum render radius set to `{radius}`.')

  @dynmap_config_render.command(name="dimension")
  @checks.admin_or_permissions()
  async def dynmap_config_render_dimension(self, ctx, dimension: int):
    """Sets the maximum X and Z coordinate that can be specified for the center of the radius render."""
    await self.config.guild(ctx.guild).render_max_dimension.set(dimension)
    await ctx.send(f'Maximum X and Z coordinate set to `{dimension}`.')

  @dynmap_config.group(name='web')
  @checks.admin_or_permissions()
  async def dynmap_config_web(self, ctx):
    """Configures dynmap web settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_web.command(name="host")
  @checks.admin_or_permissions()
  async def dynmap_config_web_host(self, ctx, host: str):
    """Sets the dynmap host URL used in the embed link."""
    await self.config.guild(ctx.guild).web_host.set(host)
    await ctx.send(f'Dynmap host URL set to `{host}`.')

  @dynmap_config_web.command(name="map")
  @checks.admin_or_permissions()
  async def dynmap_config_web_map(self, ctx, map: str):
    """Sets the dynmap map name used in the embed link."""
    await self.config.guild(ctx.guild).web_map.set(map)
    await ctx.send(f'Dynmap map name set to `{map}`.')

  @dynmap_config_web.command(name="zoom")
  @checks.admin_or_permissions()
  async def dynmap_config_web_zoom(self, ctx, zoom: int):
    """Sets the dynmap zoom level used in the embed link."""
    await self.config.guild(ctx.guild).web_zoom.set(zoom)
    await ctx.send(f'Dynmap zoom level set to `{zoom}`.')

  @dynmap_config_web.command(name="y")
  @checks.admin_or_permissions()
  async def dynmap_config_web_y(self, ctx, y: int):
    """Sets the dynmap Y coordinate used in the embed link."""
    await self.config.guild(ctx.guild).web_y.set(y)
    await ctx.send(f'Dynmap Y coordinate set to `{y}`.')

  @dynmap_config.group(name='timeout')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout(self, ctx):
    """Configures timeout settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_timeout.command(name="start")
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_start(self, ctx, timeout: int):
    """Sets the maximum number of seconds to wait for a console response after starting a dynmap render."""
    await self.config.guild(ctx.guild).start_timeout_in_seconds.set(timeout)
    await ctx.send(f'Start timeout set to `{timeout}`.')

  @dynmap_config_timeout.command(name="end")
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_end(self, ctx, timeout: int):
    """Sets the maximum number of seconds to wait for a console message indicating that a dynmap render has finished."""
    await self.config.guild(ctx.guild).end_timeout_in_seconds.set(timeout)
    await ctx.send(f'End timeout set to `{timeout}`.')

  @dynmap.command(name="render")
  async def dynmap_render(self, ctx, x: int, z: int, radius: int = None):
    """Starts a dynmap radius render centered on the specified coordinates."""
    try:
      try:
        pterodactyl_host = await self.config.guild(ctx.guild).pterodactyl_api_host()
        pterodactyl_key = await self.config.guild(ctx.guild).pterodactyl_api_key()
        pterodactyl_id = await self.config.guild(ctx.guild).pterodactyl_server_id()

        world = await self.config.guild(ctx.guild).render_world()
        default_radius = await self.config.guild(ctx.guild).render_default_radius()
        min_radius = await self.config.guild(ctx.guild).render_min_radius()
        max_radius = await self.config.guild(ctx.guild).render_max_radius()
        max_dimension = await self.config.guild(ctx.guild).render_max_dimension()

        web_host = await self.config.guild(ctx.guild).web_host()
        web_map = await self.config.guild(ctx.guild).web_map()
        web_zoom = await self.config.guild(ctx.guild).web_zoom()
        web_y = await self.config.guild(ctx.guild).web_y()

        start_timeout_in_seconds = await self.config.guild(ctx.guild).start_timeout_in_seconds()
        end_timeout_in_seconds = await self.config.guild(ctx.guild).end_timeout_in_seconds()

        if radius is None:
          radius = default_radius

        embed_url = f'{web_host}/?worldname={world}&mapname={web_map}&zoom={web_zoom}&x={x}&y={web_y}&z={z}'
        embed = self.create_embed(ctx, embed_url, radius, x, z)
        status_message = await ctx.send(embed = embed)

        if x > max_dimension or x < -max_dimension or z > max_dimension or z < -max_dimension:
          raise DynmapError(f'X and Z coordinates must be between `-{max_dimension}` and `{max_dimension}`.')
        if radius < min_radius or radius > max_radius:
          raise DynmapError(f'Radius must be between `{min_radius}` and `{max_radius}`.')

        async with ClientSession() as session:
          ws_socket, ws_token = await self.get_websocket_credentials(session, pterodactyl_host, pterodactyl_key, pterodactyl_id)

          async with session.ws_connect(ws_socket) as ws:
            await self.authenticate_websocket(ws, ws_token)
            await self.start_dynmap_render(ws, start_timeout_in_seconds, world, radius, x, z)

            embed.title = 'Dynmap Render In Progress'
            embed.color = Color.gold()

            await status_message.edit(embed = embed)

            start_time_in_seconds = timer()
            render_finished = await self.wait_for_render_to_finish(ws, end_timeout_in_seconds, world)

            if not render_finished:
              raise DynmapError('Unable to verify that the dynmap render completed successfully.')

            elapsed_time_in_seconds = int(timer() - start_time_in_seconds)
            elapsed_time_formatted = self.format_time(elapsed_time_in_seconds)

            embed.title = 'Dynmap Render Complete'
            embed.color = Color.green()
            embed.description = f'Time elapsed: {elapsed_time_formatted}'

            await status_message.edit(embed = embed)
            await status_message.add_reaction(self.UNICODE_WHITE_CHECK_MARK)

      except DynmapError as ex:
        embed.title = 'Dynmap Render Failed'
        embed.color = Color.red()
        embed.description = f'Error: {ex}'

        await status_message.edit(embed = embed)
        await status_message.add_reaction(self.UNICODE_X)
    except HTTPException as ex:
      await ctx.send('Error: Unable to edit render status message.')

  def create_embed(self, ctx, url: str, radius: int, x: int, z: int):
    embed = Embed(
      color = Color.light_grey(),
      title = 'Dynmap Render Initializing',
      description = 'Please wait...',
      url = url)

    embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
    embed.add_field(name = 'X', value = x, inline = True)
    embed.add_field(name = 'Z', value = z, inline = True)
    embed.add_field(name = 'Radius', value = radius, inline = True)

    return embed

  def format_time(self, time_in_seconds: int):
    format_minutes = int(time_in_seconds / 60)
    format_seconds = int(time_in_seconds % 60)
    return f'{format_minutes}m {format_seconds}s'

  async def get_websocket_credentials(self, session: ClientSession, host: str, key: str, id: str):
    websocket_url = reduce(urljoin, [host, 'api/client/servers/', id + '/', 'websocket'])
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {key}'
    }
    async with session.get(websocket_url, headers = headers) as response:
      status_code = response.status

      if status_code != 200:
        raise DynmapError(f'Unable to get websocket credentials. Status code: `{status_code}`.')

      response_json = await response.json()
      ws_socket = response_json['data']['socket']
      ws_token = response_json['data']['token']

      return ws_socket, ws_token

  async def authenticate_websocket(self, ws: ClientWebSocketResponse, ws_token: str):
    request_json = {
      'event': 'auth',
      'args': [ws_token]
    }

    await ws.send_json(request_json)

    try:
      response_json = await wait_for(ws.receive_json(), timeout = 10)
    except TimeoutError:
      raise DynmapError('Timed out while authenticating websocket.')

    if response_json['event'] != 'auth success':
      raise DynmapError('Received incorrect event when authenticating websocket.')

  async def start_dynmap_render(self, ws: ClientWebSocketResponse, start_timeout_in_seconds: int, world: str, radius: int, x: int, z: int):
    command = f'dynmap radiusrender {world} {x} {z} {radius}'
    request_json = {
      'event': 'send command',
      'args': [command]
    }

    await ws.send_json(request_json)

    success_response = f'Render of {radius} block radius starting on world \'{world}\'...'
    failure_response = f'Radius render of world \'{world}\' already active.'

    result = await self.wait_for_console_response(ws, start_timeout_in_seconds, success_response, failure_response)

    if result == ConsoleResponseResult.SUCCESS:
      return
    elif result == ConsoleResponseResult.FAILURE:
      raise DynmapError('A dynmap render is already running. Please try again in a few minutes.')
    else:
      raise DynmapError('Unable to verify that the dynmap render has started.')

  async def wait_for_render_to_finish(self, ws: ClientWebSocketResponse, end_timeout_in_seconds: int, world: str):
    success_response = f'Radius render of \'{world}\' finished.'

    result = await self.wait_for_console_response(ws, end_timeout_in_seconds, success_response)

    return result == ConsoleResponseResult.SUCCESS

  async def wait_for_console_response(self, ws: ClientWebSocketResponse, timeout_in_seconds: int, success_response: str, failure_response: str = None):
    start_time_in_seconds = timer()

    while timer() - start_time_in_seconds < timeout_in_seconds:
      response_json = await ws.receive_json()

      if response_json['event'] == 'console output':
        output = response_json['args'][0]

        if success_response in output:
          return ConsoleResponseResult.SUCCESS

        if failure_response is not None and failure_response in output:
          return ConsoleResponseResult.FAILURE

    return ConsoleResponseResult.TIMEOUT