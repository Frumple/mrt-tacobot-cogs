from aiohttp import ClientSession, ClientWebSocketResponse
from asyncio import sleep
from discord import Color, Embed, Message, Reaction, User
from enum import Enum
from functools import reduce
from http.client import HTTPException
from redbot.core import Config, commands, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.mod import is_mod_or_superior
from timeit import default_timer as timer
from urllib.parse import urljoin

import re

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
  """Allows users to run Dynmap radius renders on a Minecraft server hosted on Pterodactyl."""

  CONSOLE_MESSAGE_ENTITY_DATA_RETURNED = '{player} has the following entity data:'
  CONSOLE_MESSAGE_NO_ENTITY_FOUND = 'No entity was found'

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
      'render_dimension': 'overworld',
      'render_default_radius': 300,
      'render_min_radius': 100,
      'render_max_radius': 300,
      'render_max_coordinate': 30000,
      'render_queue_size': 3,
      'web_host': None,
      'web_map': 'flat',
      'web_zoom': 6,
      'web_y': 64,
      'queued_render_start_delay_in_seconds': 3,
      'elapsed_time_interval_in_seconds': 5,
      'cancellation_check_interval_in_seconds': 1,
      'auth_timeout_in_seconds': 10,
      'command_timeout_in_seconds': 10,
      'render_timeout_in_seconds': 600,
      'render_queue': []
    }
    self.config = Config.get_conf(self, identifier=8373008182, force_registration=True)
    self.config.register_guild(**default_guild)

  # Event handler when a user adds a reaction
  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User):
    guild = user.guild

    # Is the reaction a "stop button"?
    if reaction.emoji == self.UNICODE_STOP_BUTTON:
      async with self.config.guild(guild).render_queue() as render_queue:

        # Is there at least one render in the queue?
        if len(render_queue) > 0:

          # Is the reaction on the render's message?
          index, render = self.find_index_and_render_with_matching_message_id(render_queue, reaction.message.id)
          if render:

            # Is the reacting user NOT the bot?
            if user.id != self.bot.user.id:

              # Is the reacting user the one who started the render, or a staff member?
              if user.id == render['user_id'] or await is_mod_or_superior(self.bot, user):

                # If the answer is "yes" to all of the above questions, cancel the render.
                render_queue[index]['cancelling_user_id'] = user.id

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

  @dynmap_config.command(name='get_all')
  @checks.admin_or_permissions()
  async def dynmap_config_get_all(self, ctx: commands.Context):
    """Displays all settings."""
    async with self.config.guild(ctx.guild).all() as settings:
      output = '{:<40} | {:<40}\n'.format('Key', 'Value')
      for key, value in settings.items():
        if key in ['pterodactyl_api_key', 'pterodactyl_server_id']:
          value = '<redacted>'
        if isinstance(value, str) or isinstance(value, int):
          output += '{:<40} | {:<40}\n'.format(key, value)
      for page in pagify(output):
        await ctx.send(f'```{page}```')

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
    """Configures Dynmap render settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_render.command(name='world')
  @checks.admin_or_permissions()
  async def dynmap_config_render_world(self, ctx: commands.Context, world: str):
    """Sets the Minecraft world to render."""
    await self.config.guild(ctx.guild).render_world.set(world)
    await ctx.send(f'Render world set to `{world}`.')

  @dynmap_config_render.command(name='dimension')
  @checks.admin_or_permissions()
  async def dynmap_config_render_dimension(self, ctx: commands.Context, dimension: str):
    """Sets the Minecraft dimension to render. This is usually the same as the world, except if the dimension is 'overworld'."""
    await self.config.guild(ctx.guild).render_dimension.set(dimension)
    await ctx.send(f'Render dimension set to `{dimension}`.')

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

  @dynmap_config_render.command(name='max_coordinate')
  @checks.admin_or_permissions()
  async def dynmap_config_render_max_coordinate(self, ctx: commands.Context, coordinate: int):
    """Sets the maximum X and Z coordinate that can be specified for the center of the radius render."""
    await self.config.guild(ctx.guild).render_max_coordinate.set(coordinate)
    await ctx.send(f'Maximum X and Z coordinate set to `{coordinate}`.')

  @dynmap_config_render.command(name='queue_size')
  @checks.admin_or_permissions()
  async def dynmap_config_render_queue_size(self, ctx: commands.Context, size: int):
    """Sets the maximum number of renders that can be queued, including the currently running render."""
    await self.config.guild(ctx.guild).render_queue_size.set(size)
    await ctx.send(f'Render queue size set to `{size}`.')

  @dynmap_config.group(name='web')
  @checks.admin_or_permissions()
  async def dynmap_config_web(self, ctx: commands.Context):
    """Configures Dynmap web settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_web.command(name='host')
  @checks.admin_or_permissions()
  async def dynmap_config_web_host(self, ctx: commands.Context, host: str):
    """Sets the Dynmap host URL used in the embed link."""
    await self.config.guild(ctx.guild).web_host.set(host)
    await ctx.send(f'Dynmap host URL set to `{host}`.')

  @dynmap_config_web.command(name='map')
  @checks.admin_or_permissions()
  async def dynmap_config_web_map(self, ctx: commands.Context, map: str):
    """Sets the Dynmap map name used in the embed link."""
    await self.config.guild(ctx.guild).web_map.set(map)
    await ctx.send(f'Dynmap map name set to `{map}`.')

  @dynmap_config_web.command(name='zoom')
  @checks.admin_or_permissions()
  async def dynmap_config_web_zoom(self, ctx: commands.Context, zoom: int):
    """Sets the Dynmap zoom level used in the embed link."""
    await self.config.guild(ctx.guild).web_zoom.set(zoom)
    await ctx.send(f'Dynmap zoom level set to `{zoom}`.')

  @dynmap_config_web.command(name='y')
  @checks.admin_or_permissions()
  async def dynmap_config_web_y(self, ctx: commands.Context, y: int):
    """Sets the Dynmap Y coordinate used in the embed link."""
    await self.config.guild(ctx.guild).web_y.set(y)
    await ctx.send(f'Dynmap Y coordinate set to `{y}`.')

  @dynmap_config.group(name='delay')
  @checks.admin_or_permissions()
  async def dynmap_config_delay(self, ctx: commands.Context):
    """Configures delay settings."""
    if ctx.invoked_subcommand is None:
      pass

  @dynmap_config_delay.command(name='queued_render_start')
  @checks.admin_or_permissions()
  async def dynmap_config_delay_queued_render_start(self, ctx: commands.Context, delay: int):
    """Sets the number of seconds for a queued render to wait after the current render has finished."""
    await self.config.guild(ctx.guild).queue_render_delay_in_seconds.set(delay)
    await ctx.send(f'Queued render delay set to `{delay}` seconds.')

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
    await ctx.send(f'Elapsed time interval set to `{interval}` seconds.')

  @dynmap_config_interval.command(name='cancel')
  @checks.admin_or_permissions()
  async def dynmap_config_interval_cancel(self, ctx: commands.Context, interval: int):
    """While a render is in progress, check if a cancellation has been requested every X seconds."""
    await self.config.guild(ctx.guild).cancellation_check_interval_in_seconds.set(interval)
    await ctx.send(f'Cancellation check time interval set to `{interval}` seconds.')

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
    await ctx.send(f'Auth timeout set to `{timeout}` seconds.')

  @dynmap_config_timeout.command(name='command')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_command(self, ctx: commands.Context, timeout: int):
    """Sets the maximum number of seconds to wait for a console response after starting or cancelling a Dynmap render."""
    await self.config.guild(ctx.guild).command_timeout_in_seconds.set(timeout)
    await ctx.send(f'Command timeout set to `{timeout}` seconds.')

  @dynmap_config_timeout.command(name='render')
  @checks.admin_or_permissions()
  async def dynmap_config_timeout_render(self, ctx: commands.Context, timeout: int):
    """Sets the maximum number of seconds to wait for a console message indicating that a Dynmap render has finished."""
    await self.config.guild(ctx.guild).render_timeout_in_seconds.set(timeout)
    await ctx.send(f'Render timeout set to `{timeout}` seconds.')

  @dynmap.command(name='clear_queue')
  @checks.admin_or_permissions()
  async def dynmap_clear_queue(self, ctx: commands.Context):
    """Clears the internal queue of Dynmap renders. Caution: Will likely cause any currently running or queued renders to fail."""
    await self.config.guild(ctx.guild).render_queue.clear()
    await ctx.send('Render queue cleared.')

  @dynmap.command(name='render')
  async def dynmap_render(self, ctx: commands.Context, param1: str, param2: int = None, param3: int = None):
    """Starts a Dynmap radius render centered on the specified coordinates."""
    world = await self.config.guild(ctx.guild).render_world()
    dimension = await self.config.guild(ctx.guild).render_dimension()
    default_radius = await self.config.guild(ctx.guild).render_default_radius()
    min_radius = await self.config.guild(ctx.guild).render_min_radius()
    max_radius = await self.config.guild(ctx.guild).render_max_radius()
    max_coordinate = await self.config.guild(ctx.guild).render_max_coordinate()
    queue_size = await self.config.guild(ctx.guild).render_queue_size()

    this_render = None

    x = None
    z = None
    radius = None

    embed = self.create_embed(ctx)
    message = await ctx.send(embed = embed)

    try:
      async with ClientSession() as session:
        ws_socket, ws_token = await self.get_websocket_credentials(ctx, session)

        async with session.ws_connect(ws_socket) as ws:
          await self.authenticate_websocket(ctx, ws, ws_token)

          # If the 1st parameter is an integer, treat it as the X coordinate.
          # The 2nd parameter / Z coordinate must also be specified.
          if self.isinteger(param1):
            if param2 is None:
              raise RenderFailedError('The Z coordinate must be specified.')

            x = int(param1)
            z = param2
            radius = param3 if param3 is not None else default_radius

          # Otherwise, treat the 1st parameter as the player name.
          # Run "/data get entity" commands to get the current dimension and X,Z coordinates of the player.
          else:
            player_dimension = await self.get_player_dimension(
              ctx,
              session,
              ws,
              message,
              embed,
              this_render,
              param1
            )

            if player_dimension != dimension:
              raise RenderFailedError(f'Player `{param1}` must be in world `{world}` to start the render.')

            x, z = await self.get_player_coordinates(
              ctx,
              session,
              ws,
              message,
              embed,
              this_render,
              param1
            )
            radius = param2 if param2 is not None else default_radius

          embed_url = await self.get_embed_url(ctx, x, z, world)
          self.init_embed(ctx, embed, embed_url, x, z, radius)

          if x > max_coordinate or x < -max_coordinate or z > max_coordinate or z < -max_coordinate:
            raise RenderFailedError(f'X and Z coordinates must be between `-{max_coordinate}` and `{max_coordinate}`.')
          if radius < min_radius or radius > max_radius:
            raise RenderFailedError(f'Radius must be between `{min_radius}` and `{max_radius}`.')

          this_render = {
            'user_id': ctx.author.id,
            'message_id': message.id,
            'cancelling_user_id': None
          }
          async with self.config.guild(ctx.guild).render_queue() as render_queue:
            if len(render_queue) >= queue_size:
              raise RenderFailedError('Render queue is full. Please wait for a render to complete and try again.')
            render_queue.append(this_render)

          await self.start_dynmap_render(
            ctx,
            session,
            ws,
            message,
            embed,
            this_render,
            x,
            z,
            radius)

          elapsed_time_in_seconds = await self.dynmap_render_in_progress(
            ctx,
            session,
            ws,
            message,
            embed,
            this_render)
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

    # Make sure to clear out the render from the queue if it stops for any reason
    finally:
      if this_render:
        async with self.config.guild(ctx.guild).render_queue() as render_queue:
          index, render = self.find_index_and_render_with_matching_message_id(render_queue, this_render['message_id'])
          if index is not None:
            render_queue.pop(index)

  async def get_embed_url(self,
    ctx: commands.Context,
    x: int,
    z: int,
    world: str):

    web_host = await self.config.guild(ctx.guild).web_host()
    web_map = await self.config.guild(ctx.guild).web_map()
    web_zoom = await self.config.guild(ctx.guild).web_zoom()
    web_y = await self.config.guild(ctx.guild).web_y()

    return f'{web_host}/?worldname={world}&mapname={web_map}&zoom={web_zoom}&x={x}&y={web_y}&z={z}'

  async def get_websocket_credentials(self,
    ctx: commands.Context,
    session: ClientSession):

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

  async def get_player_dimension(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict,
    player_name: str):

    command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()

    dimension_command = f'data get entity {player_name} Dimension'
    dimension_request_json = self.create_command_request_json(dimension_command)

    await ws.send_json(dimension_request_json)

    success_response = self.CONSOLE_MESSAGE_ENTITY_DATA_RETURNED.format(player = player_name)
    failure_response = self.CONSOLE_MESSAGE_NO_ENTITY_FOUND

    dimension_result, dimension_output = await self.wait_for_console_response(
      ctx,
      session,
      ws,
      message,
      embed,
      this_render,
      command_timeout_in_seconds,
      success_response = success_response,
      failure_response = failure_response
    )

    dimension_output = self.strip_ansi_control_sequences(dimension_output)

    if dimension_result == ConsoleResponseResult.SUCCESS:
      regex = r'"minecraft:(?P<dimension>.+)"'
      match = re.search(regex, dimension_output)
      if match:
        return match.group('dimension')
      else:
        raise RenderFailedError(f'Received an invalid response when retrieving current world for player `{player_name}`.')
    elif dimension_result == ConsoleResponseResult.FAILURE:
      raise RenderFailedError(f'Player `{player_name}` is currently not on the Minecraft server.')
    else:
      raise RenderTimeoutError(f'Did not receive a response when retrieving current world for player `{player_name}`.')

  async def get_player_coordinates(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict,
    player_name: str):

    command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()

    position_command = f'data get entity {player_name} Pos'
    position_request_json = self.create_command_request_json(position_command)

    await ws.send_json(position_request_json)

    success_response = self.CONSOLE_MESSAGE_ENTITY_DATA_RETURNED.format(player = player_name)
    failure_response = self.CONSOLE_MESSAGE_NO_ENTITY_FOUND

    position_result, position_output = await self.wait_for_console_response(
      ctx,
      session,
      ws,
      message,
      embed,
      this_render,
      command_timeout_in_seconds,
      success_response = success_response,
      failure_response = failure_response
    )

    position_output = self.strip_ansi_control_sequences(position_output)

    if position_result == ConsoleResponseResult.SUCCESS:
      regex = r'\[(?P<x>-?\d+.\d+)d, (?P<y>-?\d+.\d+)d, (?P<z>-?\d+.\d+)d\]'
      match = re.search(regex, position_output)
      if match:
        x = int(float(match.group('x')))
        z = int(float(match.group('z')))
        return x, z
      else:
        raise RenderFailedError(f'Received an invalid response when retrieving current coordinates for player `{player_name}`.')
    elif position_result == ConsoleResponseResult.FAILURE:
      raise RenderFailedError(f'Player `{player_name}` is currently not on the Minecraft server.')
    else:
      raise RenderTimeoutError(f'Did not receive a response when retrieving current coordinates for player `{player_name}`.')

  async def start_dynmap_render(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict,
    x: int,
    z: int,
    radius: int):

    world = await self.config.guild(ctx.guild).render_world()
    queued_render_start_delay_in_seconds = await self.config.guild(ctx.guild).queued_render_start_delay_in_seconds()
    command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()
    render_timeout_in_seconds = await self.config.guild(ctx.guild).render_timeout_in_seconds()

    command = f'dynmap radiusrender {world} {x} {z} {radius}'
    request_json = self.create_command_request_json(command)

    while True:
      start_render_result = ConsoleResponseResult.FAILURE

      # Attempt to start the render only if it is the next queued render to run
      async with self.config.guild(ctx.guild).render_queue() as render_queue:
        if len(render_queue) > 0 and render_queue[0]['message_id'] == this_render['message_id']:
          await ws.send_json(request_json)

          success_response = self.CONSOLE_MESSAGE_RENDER_STARTED.format(radius = radius, world = world)
          failure_response = self.CONSOLE_MESSAGE_RENDER_ALREADY_RUNNING.format(world = world)

          start_render_result, start_render_output = await self.wait_for_console_response(
            ctx,
            session,
            ws,
            message,
            embed,
            this_render,
            command_timeout_in_seconds,
            success_response = success_response,
            failure_response = failure_response)

      # If the render has started, return successfully
      if start_render_result == ConsoleResponseResult.SUCCESS:
        await self.update_status_message(message, embed,
          title = 'Dynmap Render In Progress',
          color = Color.gold(),
          description = 'Time elapsed: 0m 0s',
          footer = f'React with {self.UNICODE_STOP_BUTTON} to cancel (Initiating user or staff only).',
          reaction = self.UNICODE_STOP_BUTTON
        )
        return

      # If another render is already running...
      elif start_render_result == ConsoleResponseResult.FAILURE:

        # ...and the other render was initiated in-game and not through the bot, fail this render immediately
        if render_queue[0]['message_id'] == this_render['message_id']:
          raise RenderFailedError('An in-game render is currently running. Please try again in a few minutes.')

        # Otherwise, wait for the other render to finish or be cancelled, then try to start this render again
        await self.update_status_message(message, embed,
          title = 'Dynmap Render Queued',
          color = Color.blue(),
          description = 'Another render is currently running. Please wait...',
          footer = f'React with {self.UNICODE_STOP_BUTTON} to cancel (Initiating user or staff only).',
          reaction = self.UNICODE_STOP_BUTTON
        )

        success_response = self.CONSOLE_MESSAGE_RENDER_FINISHED.format(world = world)
        failure_response = self.CONSOLE_MESSAGE_RENDER_CANCELLED.format(world = world)

        console_result, console_output = await self.wait_for_console_response(
          ctx,
          session,
          ws,
          message,
          embed,
          this_render,
          render_timeout_in_seconds,
          success_response = success_response,
          failure_response = failure_response,
          cancellable = True
        )

        if console_result == ConsoleResponseResult.TIMEOUT:
          raise RenderTimeoutError('Waited too long for the current render to finish or be cancelled.')

        # Wait a few seconds to let the previous render remove itself from the queue, then try to start the render again
        await sleep(queued_render_start_delay_in_seconds)

      else:
        raise RenderTimeoutError('Did not receive a response when starting the render.')

  async def dynmap_render_in_progress(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict):

    world = await self.config.guild(ctx.guild).render_world()

    render_timeout_in_seconds = await self.config.guild(ctx.guild).render_timeout_in_seconds()

    success_response = self.CONSOLE_MESSAGE_RENDER_FINISHED.format(world = world)

    start_time_in_seconds = timer()

    console_result, console_output = await self.wait_for_console_response(
      ctx,
      session,
      ws,
      message,
      embed,
      this_render,
      render_timeout_in_seconds,
      success_response = success_response,
      show_elapsed_time = True,
      cancellable = True,
      run_command_when_cancelled = True
    )

    if console_result == ConsoleResponseResult.SUCCESS:
      elapsed_time_in_seconds = int(timer() - start_time_in_seconds)
      return elapsed_time_in_seconds

    raise RenderTimeoutError('Unable to verify that the dynmap render completed successfully.')

  async def cancel_dynmap_render(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict,
    cancelling_user: User,
    run_command_when_cancelled: bool):

    cancel_render_result = ConsoleResponseResult.SUCCESS

    if run_command_when_cancelled:
      world = await self.config.guild(ctx.guild).render_world()
      command_timeout_in_seconds = await self.config.guild(ctx.guild).command_timeout_in_seconds()

      command = f'dynmap cancelrender {world}'
      request_json = self.create_command_request_json(command)

      await ws.send_json(request_json)

      success_response = self.CONSOLE_MESSAGE_RENDER_CANCELLED.format(world = world)

      cancel_render_result, cancel_render_output = await self.wait_for_console_response(
        ctx,
        session,
        ws,
        message,
        embed,
        this_render,
        command_timeout_in_seconds,
        success_response = success_response)

    if cancel_render_result == ConsoleResponseResult.SUCCESS:
      raise RenderCancelledError(f'Cancelled by {cancelling_user.mention}.')
    else:
      raise RenderTimeoutError('Did not receive a response when cancelling the render.')

  async def wait_for_console_response(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    message: Message,
    embed: Embed,
    this_render: dict,
    timeout_in_seconds: int,
    *,
    success_response: str = None,            # If a received console message contains this text, return a "SUCCESS" result.
    failure_response: str = None,            # If a received console message contains this text, return a "FAILURE" result.
    show_elapsed_time: bool = False,         # Set to True to show the elapsed time in the description while waiting for a response
    cancellable: bool = False,               # Set to True if the render can be cancelled
    run_command_when_cancelled: bool = False # Set to True if the "/dynmap cancelrender" command should be run when the render is cancelled
    ):

    elapsed_time_interval_in_seconds = await self.config.guild(ctx.guild).elapsed_time_interval_in_seconds()
    cancellation_check_interval_in_seconds = await self.config.guild(ctx.guild).cancellation_check_interval_in_seconds()

    start_time_in_seconds = timer()
    current_time_in_seconds = start_time_in_seconds
    last_elapsed_time_update_in_seconds = start_time_in_seconds
    last_cancellation_check_in_seconds = start_time_in_seconds

    while current_time_in_seconds - start_time_in_seconds < timeout_in_seconds:
      event_json = await ws.receive_json()
      console_output = await self.handle_websocket_event(
        ctx,
        session,
        ws,
        event_json)

      current_time_in_seconds = timer()
      elapsed_time_in_seconds = int(current_time_in_seconds - start_time_in_seconds)

      if console_output:
        if success_response and success_response.casefold() in console_output.casefold():
          return ConsoleResponseResult.SUCCESS, console_output

        if failure_response and failure_response.casefold() in console_output.casefold():
          return ConsoleResponseResult.FAILURE, console_output

      # If elapsed time is shown, update it in the description every 5 seconds
      if show_elapsed_time:
        if current_time_in_seconds - last_elapsed_time_update_in_seconds >= elapsed_time_interval_in_seconds:
          elapsed_time_in_seconds = int(elapsed_time_in_seconds / elapsed_time_interval_in_seconds) * elapsed_time_interval_in_seconds
          elapsed_time_formatted = self.format_time(elapsed_time_in_seconds)
          embed.description = f'Time elapsed: {elapsed_time_formatted}'
          await message.edit(embed = embed)

          last_elapsed_time_update_in_seconds = current_time_in_seconds

      # If this render can be cancelled, check for render cancellations every second
      if cancellable:
        if current_time_in_seconds - last_cancellation_check_in_seconds >= cancellation_check_interval_in_seconds:
          async with self.config.guild(ctx.guild).render_queue() as render_queue:
            index, render = self.find_index_and_render_with_matching_message_id(render_queue, this_render['message_id'])
            if render:
              cancelling_user_id = render['cancelling_user_id']
              if cancelling_user_id:
                cancelling_user = self.bot.get_user(cancelling_user_id)
                if cancelling_user:
                  await self.cancel_dynmap_render(
                    ctx,
                    session,
                    ws,
                    message,
                    embed,
                    this_render,
                    cancelling_user,
                    run_command_when_cancelled)
                else:
                  raise RenderFailedError('Cancelling user was not found.')

              last_cancellation_check_in_seconds = current_time_in_seconds

            else:
              raise RenderFailedError('Render is missing from the render queue.')

    return ConsoleResponseResult.TIMEOUT, None

  # Processes incoming events from the Pterodactyl API websocket.
  # Ensures that the websocket token is re-authenticated when it is expiring or expired.
  # If the event is 'console output', return the output. Otherwise, return None.
  async def handle_websocket_event(self,
    ctx: commands.Context,
    session: ClientSession,
    ws: ClientWebSocketResponse,
    event_json: str):

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
    footer: str = None,
    reaction: str = None):

    embed.title = title
    embed.color = color
    embed.description = description
    embed.set_footer(text = footer)

    await message.edit(embed = embed)

    await message.clear_reactions()

    if reaction:
      await message.add_reaction(reaction)

  @staticmethod
  def create_embed(ctx):
    embed = Embed(
      color = Color.light_grey(),
      title = 'Dynmap Render Initializing',
      description = 'Please wait...')

    embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar)

    return embed

  @staticmethod
  def init_embed(ctx, embed: Embed, url: str, x: int, z: int, radius: int):
    embed.url = url

    embed.add_field(name = 'X', value = x, inline = True)
    embed.add_field(name = 'Z', value = z, inline = True)
    embed.add_field(name = 'Radius', value = radius, inline = True)

    return embed

  @staticmethod
  def create_command_request_json(command: str):
    return {
      'event': 'send command',
      'args': [command]
    }

  @staticmethod
  def format_time(time_in_seconds: int):
    format_minutes = int(time_in_seconds / 60)
    format_seconds = int(time_in_seconds % 60)
    return f'{format_minutes}m {format_seconds}s'

  @staticmethod
  def find_index_and_render_with_matching_message_id(render_queue, message_id):
    return next(((i, v) for (i, v) in enumerate(render_queue) if v['message_id'] == message_id), (None, None))

  @staticmethod
  def isinteger(s):
    return s[1:].isnumeric() if s[0] == '-' else s.isnumeric()

  @staticmethod
  def strip_ansi_control_sequences(s):
    return re.sub(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]', '', s)
