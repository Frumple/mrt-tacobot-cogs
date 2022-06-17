from aiohttp import ClientSession, ClientWebSocketResponse
from asyncio import TimeoutError, wait_for
from discord import Color, Embed, Message, Reaction, User
from enum import Enum
from functools import reduce
from http.client import HTTPException
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
from redbot.core.utils.mod import is_mod_or_superior
from timeit import default_timer as timer
from urllib.parse import urljoin

class ConsoleResponseResult(Enum):
  SUCCESS = 1
  FAILURE = 2
  TIMEOUT = 3

class RenderCancelledError(Exception):
  pass

class RenderFailedError(Exception):
  pass

class RenderTimeoutError(Exception):
  pass

class Dynmap(commands.Cog):
  """Allows users to run dynmap radius renders from Discord."""

  CONSOLE_MESSAGE_RENDER_STARTED = 'Render of {radius} block radius starting on world \'{world}\'...'
  CONSOLE_MESSAGE_RENDER_ALREADY_RUNNING = 'Radius render of world \'{world}\' already active.'
  CONSOLE_MESSAGE_RENDER_FINISHED = 'Radius render of \'{world}\' finished.'
  CONSOLE_MESSAGE_RENDER_CANCELLED = 'Cancelled render for \'{world}\''

  UNICODE_WHITE_CHECK_MARK = '\U00002705'
  UNICODE_X = '\U0000274C'
  UNICODE_STOP_BUTTON = '\U000023F9'

  def __init__(self, bot: Red):
    self.bot = bot

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
      'elapsed_time_interval_in_seconds': 5,
      'cancellation_check_interval_in_seconds': 1,
      'auth_timeout_in_seconds': 10,
      'command_timeout_in_seconds': 10,
      'render_timeout_in_seconds': 600,
      'current_render': None
    }
    self.config = Config.get_conf(self, identifier=8373008182, force_registration=True)
    self.config.register_guild(**default_guild)

  @commands.group()
  async def dynmap(self, ctx: commands.Context):
    if ctx.invoked_subcommand is None:
      pass

  @dynmap.group(name='config')
  @checks.admin_or_permissions()
  async def dynmap_config(self, ctx: commands.Context):
    """Configures settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config.group(name='pterodactyl')
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl(self, ctx: commands.Context):
    """Configures Pterodactyl connection settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_pterodactyl.command(name='host')
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_host(self, ctx: commands.Context, host: str):
    """Sets the Pterodactyl API host URL."""
    await self.config.guild(ctx.guild).pterodactyl_api_host.set(host)
    await ctx.send(f'Pterodactyl API host URL has been set to `{host}`.')

  @dynmap_config_pterodactyl.command(name='key')
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_key(self, ctx: commands.Context, key: str):
    """Sets the Pterodactyl API client key."""
    await self.config.guild(ctx.guild).pterodactyl_api_key.set(key)
    await ctx.send('Pterodactyl API client key has been set.')

  @dynmap_config_pterodactyl.command(name='id')
  @checks.admin_or_permissions()
  async def dynmap_config_pterodactyl_id(self, ctx: commands.Context, id: str):
    """Sets the Pterodactyl server ID."""
    await self.config.guild(ctx.guild).pterodactyl_server_id.set(id)
    await ctx.send(f'Pterodactyl API server ID has been set.')

  @dynmap_config.group(name='render')
  @checks.admin_or_permissions()
  async def dynmap_config_render(self, ctx: commands.Context):
    """Configures dynmap render settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_render.command(name='world')
  @checks.admin_or_permissions()
  async def dynmap_config_render_world(self, ctx: commands.Context, world: str):
    """Sets the world to render."""
    await self.config.guild(ctx.guild).render_world.set(world)
    await ctx.send(f'Render world set to `{world}`.')

  @dynmap_config_render.command(name='default_radius')
  @checks.admin_or_permissions()
  async def dynmap_config_render_default_radius(self, ctx: commands.Context, radius: int):
    """Sets the default render radius (when radius is not specified in the render command)."""
    await self.config.guild(ctx.guild).render_min_radius.set(radius)
    await ctx.send(f'Default render radius set to `{radius}`.')

  @dynmap_config_render.command(name='min_radius')
  @checks.admin_or_permissions()
  async def dynmap_config_render_min_radius(self, ctx: commands.Context, radius: int):
    """Sets the minimum render radius."""
    await self.config.guild(ctx.guild).render_min_radius.set(radius)
    await ctx.send(f'Minimum render radius set to `{radius}`.')

  @dynmap_config_render.command(name='max_radius')
  @checks.admin_or_permissions()
  async def dynmap_config_render_max_radius(self, ctx: commands.Context, radius: int):
    """Sets the maximum render radius."""
    await self.config.guild(ctx.guild).render_max_radius.set(radius)
    await ctx.send(f'Maximum render radius set to `{radius}`.')

  @dynmap_config_render.command(name='dimension')
  @checks.admin_or_permissions()
  async def dynmap_config_render_dimension(self, ctx: commands.Context, dimension: int):
    """Sets the maximum X and Z coordinate that can be specified for the center of the radius render."""
    await self.config.guild(ctx.guild).render_max_dimension.set(dimension)
    await ctx.send(f'Maximum X and Z coordinate set to `{dimension}`.')

  @dynmap_config.group(name='web')
  @checks.admin_or_permissions()
  async def dynmap_config_web(self, ctx: commands.Context):
    """Configures dynmap web settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_web.command(name='host')
  @checks.admin_or_permissions()
  async def dynmap_config_web_host(self, ctx: commands.Context, host: str):
    """Sets the dynmap host URL used in the embed link."""
    await self.config.guild(ctx.guild).web_host.set(host)
    await ctx.send(f'Dynmap host URL set to `{host}`.')

  @dynmap_config_web.command(name='map')
  @checks.admin_or_permissions()
  async def dynmap_config_web_map(self, ctx: commands.Context, map: str):
    """Sets the dynmap map name used in the embed link."""
    await self.config.guild(ctx.guild).web_map.set(map)
    await ctx.send(f'Dynmap map name set to `{map}`.')

  @dynmap_config_web.command(name='zoom')
  @checks.admin_or_permissions()
  async def dynmap_config_web_zoom(self, ctx: commands.Context, zoom: int):
    """Sets the dynmap zoom level used in the embed link."""
    await self.config.guild(ctx.guild).web_zoom.set(zoom)
    await ctx.send(f'Dynmap zoom level set to `{zoom}`.')

  @dynmap_config_web.command(name='y')
  @checks.admin_or_permissions()
  async def dynmap_config_web_y(self, ctx: commands.Context, y: int):
    """Sets the dynmap Y coordinate used in the embed link."""
    await self.config.guild(ctx.guild).web_y.set(y)
    await ctx.send(f'Dynmap Y coordinate set to `{y}`.')

  @dynmap_config.group(name='interval')
  @checks.admin_or_permissions()
  async def dynmap_config_interval(self, ctx: commands.Context):
    """Configures interval settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_interval.command(name='elapsed')
  @checks.admin_or_permissions()
  async def dynmap_config_interval_elapsed(self, ctx: commands.Context, interval: int):
    """While a render is in progress, update the elapsed time every X seconds."""
    await self.config.guild(ctx.guild).elapsed_time_interval_in_seconds.set(interval)
    await ctx.send(f'Elapsed time interval set to `{interval}`.')

  @dynmap_config_interval.command(name='cancel')
  @checks.admin_or_permissions()
  async def dynmap_config_interval_cancel(self, ctx: commands.Context, interval: int):
    """While a render is in progress, check if a cancellation has been requested every X seconds."""
    await self.config.guild(ctx.guild).cancellation_check_interval_in_seconds.set(interval)
    await ctx.send(f'Cancellation check time interval set to `{interval}`.')

  @dynmap_config.group(name='timeout')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout(self, ctx: commands.Context):
    """Configures timeout settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_timeout.command(name='auth')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_auth(self, ctx: commands.Context, timeout: int):
    """Sets the maximum number of seconds to wait for a successful response after sending a websocket authentication request.'."""
    await self.config.guild(ctx.guild).auth_timeout_in_seconds.set(timeout)
    await ctx.send(f'Auth timeout set to `{timeout}`.')

  @dynmap_config_timeout.command(name='command')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_command(self, ctx: commands.Context, timeout: int):
    """Sets the maximum number of seconds to wait for a console response after starting or cancelling a dynmap render."""
    await self.config.guild(ctx.guild).command_timeout_in_seconds.set(timeout)
    await ctx.send(f'Command timeout set to `{timeout}`.')

  @dynmap_config_timeout.command(name='render')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_render(self, ctx: commands.Context, timeout: int):
    """Sets the maximum number of seconds to wait for a console message indicating that a dynmap render has finished."""
    await self.config.guild(ctx.guild).render_timeout_in_seconds.set(timeout)
    await ctx.send(f'Render timeout set to `{timeout}`.')

  @dynmap.command(name='render')
  async def dynmap_render(self, ctx: commands.Context, x: int, z: int, radius: int = None):
    """Starts a dynmap radius render centered on the specified coordinates."""
    world = await self.config.guild(ctx.guild).render_world()
    default_radius = await self.config.guild(ctx.guild).render_default_radius()
    min_radius = await self.config.guild(ctx.guild).render_min_radius()
    max_radius = await self.config.guild(ctx.guild).render_max_radius()
    max_dimension = await self.config.guild(ctx.guild).render_max_dimension()

    this_render = None

    try:
      try:
        if radius is None:
          radius = default_radius

        embed_url = await self.get_embed_url(ctx, x, z, world)
        embed = self.create_embed(ctx, embed_url, radius, x, z)
        message = await ctx.send(embed = embed)

        if x > max_dimension or x < -max_dimension or z > max_dimension or z < -max_dimension:
          raise RenderFailedError(f'X and Z coordinates must be between `-{max_dimension}` and `{max_dimension}`.')
        if radius < min_radius or radius > max_radius:
          raise RenderFailedError(f'Radius must be between `{min_radius}` and `{max_radius}`.')

        async with ClientSession() as session:
          ws_socket, ws_token = await self.get_websocket_credentials(ctx, session)

          async with session.ws_connect(ws_socket) as ws:
            await self.authenticate_websocket(ctx, ws, ws_token)

            this_render = {
              'user_id': ctx.author.id,
              'message_id': message.id,
              'cancelling_user_id': None
            }
            await self.config.guild(ctx.guild).current_render.set(this_render)

            await self.start_dynmap_render(
              ctx,
              session,
              ws,
              embed,
              message,
              x,
              z,
              radius)

            elapsed_time_in_seconds = await self.dynmap_render_in_progress(
              ctx,
              session,
              ws,
              embed,
              message)
            elapsed_time_formatted = self.format_time(elapsed_time_in_seconds)

            await self.update_status_message(message, embed,
              title = 'Dynmap Render Complete',
              color = Color.green(),
              description = f'Time elapsed: {elapsed_time_formatted}',
              reaction = self.UNICODE_WHITE_CHECK_MARK
            )

      except RenderCancelledError as ex:
        await self.update_status_message(message, embed,
          title = 'Dynmap Render Cancelled',
          color = Color.red(),
          description = f'{ex}',
          reaction = self.UNICODE_X
        )

      except RenderFailedError as ex:
        await self.update_status_message(message, embed,
          title = 'Dynmap Render Failed',
          color = Color.red(),
          description = f'Error: {ex}',
          reaction = self.UNICODE_X
        )

      except RenderTimeoutError as ex:
        await self.update_status_message(message, embed,
          title = 'Dynmap Render Timeout',
          color = Color.red(),
          description = f'Error: {ex}',
          reaction = self.UNICODE_X
        )

    except HTTPException as ex:
      await ctx.send('Error: Unable to edit render status message.')

    # Remember to clear out the current render information if the render stops for any reason
    current_render = await self.config.guild(ctx.guild).current_render()
    if this_render and this_render is current_render:
      await self.config.guild(ctx.guild).current_render.clear()

  async def get_embed_url(self, ctx, x, z, world):
    web_host = await self.config.guild(ctx.guild).web_host()
    web_map = await self.config.guild(ctx.guild).web_map()
    web_zoom = await self.config.guild(ctx.guild).web_zoom()
    web_y = await self.config.guild(ctx.guild).web_y()

    return f'{web_host}/?worldname={world}&mapname={web_map}&zoom={web_zoom}&x={x}&y={web_y}&z={z}'

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

  def create_command_request_json(self, command: str):
    return {
      'event': 'send command',
      'args': [command]
    }

  def format_time(self, time_in_seconds: int):
    format_minutes = int(time_in_seconds / 60)
    format_seconds = int(time_in_seconds % 60)
    return f'{format_minutes}m {format_seconds}s'

  async def get_websocket_credentials(self, ctx: commands.Context, session: ClientSession):
    pterodactyl_host = await self.config.guild(ctx.guild).pterodactyl_api_host()
    pterodactyl_key = await self.config.guild(ctx.guild).pterodactyl_api_key()
    pterodactyl_id = await self.config.guild(ctx.guild).pterodactyl_server_id()

    websocket_url = reduce(urljoin, [pterodactyl_host, 'api/client/servers/', pterodactyl_id + '/', 'websocket'])
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {pterodactyl_key}'
    }
    async with session.get(websocket_url, headers = headers) as response:
      status_code = response.status

      if status_code != 200:
        raise RenderFailedError(f'Unable to get websocket credentials. Status code: `{status_code}`.')

      response_json = await response.json()
      ws_socket = response_json['data']['socket']
      ws_token = response_json['data']['token']

      return ws_socket, ws_token

  async def authenticate_websocket(self,
    ctx: commands.Context,
    ws: ClientWebSocketResponse,
    ws_token: str):
    auth_timeout_in_seconds = await self.config.guild(ctx.guild).auth_timeout_in_seconds()

    request_json = {
      'event': 'auth',
      'args': [ws_token]
    }

    await ws.send_json(request_json)

    start_time_in_seconds = timer()

    while timer() - start_time_in_seconds < auth_timeout_in_seconds:
      event_json = await ws.receive_json()

      if event_json['event'] == 'auth success':
        return

    raise RenderTimeoutError('Timed out while authenticating websocket.')

  async def start_dynmap_render(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    embed: Embed,
    message: Message,
    x: int,
    z: int,
    radius: int):

    world = await self.config.guild(ctx.guild).render_world()
    command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()
    render_timeout_in_seconds = await self.config.guild(ctx.guild).render_timeout_in_seconds()

    command = f'dynmap radiusrender {world} {x} {z} {radius}'
    request_json = self.create_command_request_json(command)

    while True:
      # TODO: Start render only if it is the next render to run

      await ws.send_json(request_json)

      success_response = self.CONSOLE_MESSAGE_RENDER_STARTED.format(radius = radius, world = world)
      failure_response = self.CONSOLE_MESSAGE_RENDER_ALREADY_RUNNING.format(world = world)

      start_render_result = await self.wait_for_console_response(
        ctx,
        session,
        ws,
        command_timeout_in_seconds,
        success_response,
        failure_response)

      current_render = await self.config.guild(ctx.guild).current_render()

      # If another render is already running, wait for it to finish or be cancelled, then try to start the render again
      if start_render_result == ConsoleResponseResult.FAILURE:
        # TODO: Add render to queue

        await self.update_status_message(message, embed,
          title = 'Dynmap Render Queued',
          color = Color.blue(),
          description = 'Another render is currently running. Please wait...'
        )

        success_response = self.CONSOLE_MESSAGE_RENDER_FINISHED.format(world = world)
        failure_response = self.CONSOLE_MESSAGE_RENDER_CANCELLED.format(world = world)

        result = await self.wait_for_console_response(
          ctx,
          session,
          ws,
          render_timeout_in_seconds,
          success_response,
          failure_response
        )

        if result == ConsoleResponseResult.TIMEOUT:
          raise RenderTimeoutError('Waited too long for the current render to finish or be cancelled.')

      # TODO: Fail if queue is full
      # raise RenderFailedError('A dynmap render is already running. Please try again in a few minutes.')

      # If the render has started, return successfully
      elif start_render_result == ConsoleResponseResult.SUCCESS:
        await self.update_status_message(message, embed,
          title = 'Dynmap Render In Progress',
          color = Color.gold(),
          description = 'Time elapsed: 0m 0s',
          footer = f'React with {self.UNICODE_STOP_BUTTON} to cancel (Initiating user or staff only).',
          reaction = self.UNICODE_STOP_BUTTON
        )

        return

      else:
        raise RenderTimeoutError('Did not receive a response when starting the render.')

  async def dynmap_render_in_progress(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    embed: Embed,
    message: Message):

    world = await self.config.guild(ctx.guild).render_world()

    elapsed_time_interval_in_seconds = await self.config.guild(ctx.guild).elapsed_time_interval_in_seconds()
    cancellation_check_interval_in_seconds = await self.config.guild(ctx.guild).cancellation_check_interval_in_seconds()

    command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()
    render_timeout_in_seconds = await self.config.guild(ctx.guild).render_timeout_in_seconds()

    success_response = self.CONSOLE_MESSAGE_RENDER_FINISHED.format(world = world)
    start_time_in_seconds = timer()
    current_time_in_seconds = start_time_in_seconds

    last_elapsed_time_update_in_seconds = start_time_in_seconds
    last_cancellation_check_in_seconds = start_time_in_seconds

    while current_time_in_seconds - start_time_in_seconds < render_timeout_in_seconds:
      event_json = await ws.receive_json()
      print(event_json, flush = True)

      current_time_in_seconds = timer()
      elapsed_time_in_seconds = int(current_time_in_seconds - start_time_in_seconds)

      console_output = await self.handle_websocket_event(
        ctx,
        session,
        ws,
        event_json
      )

      # Return when a "render finished" console message is encountered
      if console_output and success_response in console_output:
        return elapsed_time_in_seconds

      # Update the time elapsed text every 5 seconds
      if current_time_in_seconds - last_elapsed_time_update_in_seconds >= elapsed_time_interval_in_seconds:
        elapsed_time_in_seconds = int(elapsed_time_in_seconds / elapsed_time_interval_in_seconds) * elapsed_time_interval_in_seconds
        elapsed_time_formatted = self.format_time(elapsed_time_in_seconds)
        embed.description = f'Time elapsed: {elapsed_time_formatted}'
        await message.edit(embed = embed)

        last_elapsed_time_update_in_seconds = current_time_in_seconds

      # Check for render cancellations every second
      if current_time_in_seconds - last_cancellation_check_in_seconds >= cancellation_check_interval_in_seconds:
        current_render = await self.config.guild(ctx.guild).current_render()
        cancelling_user_id = current_render['cancelling_user_id']

        if cancelling_user_id:
          cancelling_user = self.bot.get_user(cancelling_user_id)
          if cancelling_user:
            await self.cancel_dynmap_render(
              ctx,
              session,
              ws,
              cancelling_user,
              command_timeout_in_seconds,
              world)
          else:
            raise RenderFailedError('Cancelling user was not found.')

        last_cancellation_check_in_seconds = current_time_in_seconds

    raise RenderTimeoutError('Unable to verify that the dynmap render completed successfully.')

  # Event handler when a user adds a reaction
  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User):
    guild = user.guild

    # Is the reaction a "stop button"?
    if reaction.emoji == self.UNICODE_STOP_BUTTON:
      current_render = await self.config.guild(guild).current_render()

      # Is there a render currently running?
      if current_render:

        # Is the reaction on the render's message?
        if reaction.message.id == current_render['message_id']:

          # Is the reacting user NOT the bot?
          if user.id != self.bot.user.id:

            # Is the reacting user the one who started the render, or a staff member?
            if user.id == current_render['user_id'] or await is_mod_or_superior(self.bot, user):

              # If the answer is "yes" to all of the above questions, cancel the render.
              current_render['cancelling_user_id'] = user.id
              await self.config.guild(guild).current_render.set(current_render)

  async def cancel_dynmap_render(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    cancelling_user: User,
    command_timeout_in_seconds: int,
    world: str):

    command = f'dynmap cancelrender {world}'
    request_json = self.create_command_request_json(command)

    await ws.send_json(request_json)

    success_response = self.CONSOLE_MESSAGE_RENDER_CANCELLED.format(world = world)

    result = await self.wait_for_console_response(
      ctx,
      session,
      ws,
      command_timeout_in_seconds,
      success_response)

    if result == ConsoleResponseResult.SUCCESS:
      raise RenderCancelledError(f'Cancelled by {cancelling_user.mention}.')
    else:
      raise RenderTimeoutError('Did not receive a response when cancelling the render.')

  async def wait_for_console_response(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    timeout_in_seconds: int,
    success_response: str,
    failure_response: str = None):

    start_time_in_seconds = timer()

    while timer() - start_time_in_seconds < timeout_in_seconds:
      event_json = await ws.receive_json()
      console_output = await self.handle_websocket_event(
        ctx,
        session,
        ws,
        event_json)

      if console_output:
        if success_response in console_output:
          return ConsoleResponseResult.SUCCESS

        if failure_response and failure_response in console_output:
          return ConsoleResponseResult.FAILURE

    return ConsoleResponseResult.TIMEOUT

  # Processes incoming events from the Pterodactyl API websocket.
  # Ensures that the websocket token is re-authenticated when it is expiring or expired.
  # If the event is 'console output', return the output. Otherwise, return None.
  async def handle_websocket_event(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    event_json: str
  ):
    event = event_json['event']

    if event == 'console output':
      arg = event_json['args'][0]
      return arg

    elif event == 'jwt error':
      arg = event_json['args'][0]
      if arg == 'jwt: exp claim is invalid':
        raise RenderFailedError('Websocket token expired.')
      else:
        print(f'JWT Error: {arg}', flush = True)
        raise RenderFailedError('Websocket failure. Check your console or logs for details.')

    elif event == 'token expiring' or event == 'token expired':
      ws_socket, ws_token = await self.get_websocket_credentials(ctx, session)
      await self.authenticate_websocket(ctx, ws, ws_token)

    return None

  async def update_status_message(self,
    message: Message,
    embed: Embed,
    *,
    title: str = None,
    color: Color = None,
    description: str = None,
    footer: str = Embed.Empty,
    reaction: str = None):

    embed.title = title
    embed.color = color
    embed.description = description
    embed.set_footer(text = footer)

    await message.edit(embed = embed)

    await message.clear_reactions()

    if reaction:
      await message.add_reaction(reaction)
