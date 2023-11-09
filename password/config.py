from discord import ButtonStyle, Interaction, PartialEmoji, TextChannel
from discord.errors import HTTPException, NotFound
from discord.ui import Button, View
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

class PasswordButton(Button):
  def __init__(self, service_name: str, service: dict, log_channel: TextChannel = None, response_lifespan: int = None):
    # Setting the custom_id to a unique value ensures the view is persistent
    super().__init__(
      custom_id = service_name
    )
    self.label = service['button_text']
    self.style = getattr(ButtonStyle, service['style']) if 'style' in service and service['style'] is not None else ButtonStyle.primary
    self.emoji = PartialEmoji.from_str(service['emoji']) if 'emoji' in service and service['emoji'] is not None else None

    self.service_name = service_name
    self.service = service
    self.log_channel = log_channel
    self.response_lifespan = response_lifespan

  async def callback(self, interaction: Interaction):
    description = self.service['description']
    password = self.service['password']
    text = f'{description}: `{password}`'

    # If log channel is defined, record the password retrieval to it
    if self.log_channel is not None:
      await self.log_channel.send(f'{interaction.user.mention} has requested the password for `{self.service_name}`.')

    # Send the password only to the user
    await interaction.response.send_message(text, ephemeral = True, delete_after = self.response_lifespan)

class PasswordView(View):
  def __init__(self, config: Config, log_channel: TextChannel = None, response_lifespan: int = None):
    # Setting the timeout to None ensures the view is persistent
    super().__init__(
      timeout = None
    )
    self.config = config
    self.log_channel = log_channel
    self.response_lifespan = response_lifespan

  async def createButtons(self):
    self.clear_items()
    async with self.config.services() as services:
      for service_name, service in services.items():
        button = PasswordButton(service_name, service, self.log_channel, self.response_lifespan)
        self.add_item(button)

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

  @password_config.command(name='set_message_channel')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_message_channel(self, ctx: commands.Context, channel: TextChannel) -> None:
    """Sets the channel that contains the message."""
    await self.config.message_channel_id.set(channel.id)
    await ctx.send(f'Password message channel has been set to: {channel.mention}')
    await self.password_config_update(ctx)

  @password_config.command(name='set_message_text')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_message_text(self, ctx: commands.Context, *, message_text: str) -> None:
    """Sets the text of the message."""
    await self.config.message_text.set(message_text)
    await ctx.send(f'Password message text has been set to: {message_text}')
    await self.password_config_update(ctx)

  @password_config.command(name='set_log_channel')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_log_channel(self, ctx: commands.Context, channel: TextChannel = None) -> None:
    """Sets the optional channel that logs all password retrievals."""
    if channel is None:
      await self.config.log_channel_id.clear()
      await ctx.send('Password log channel is now disabled.')
    else:
      await self.config.log_channel_id.set(channel.id)
      await ctx.send(f'Password log channel has been set to: {channel.mention}')
    await self.password_config_update(ctx)

  @password_config.command(name='set_response_lifespan')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_response_lifespan(self, ctx: commands.Context, lifespan: int = None) -> None:
    """Sets the number of seconds a password response message should exist before being automatically deleted."""
    if lifespan is None:
      await self.config.response_lifespan.clear()
      await ctx.send('Response lifespan is now disabled.')
    else:
      await self.config.response_lifespan.set(lifespan)
      await ctx.send(f'Response lifespan has been set to: {lifespan} seconds')
    await self.password_config_update(ctx)

  @password_config.command(name='list_services')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_list_services(self, ctx: commands.Context) -> None:
    """Lists all services."""
    async with self.config.services() as services:
      for key, value in services.items():
        button_text = value['button_text']
        description = value['description']
        password = value['password']
        style = value['style'] if 'style' in value else None
        emoji = value['emoji'] if 'emoji' in value else None

        text = f'**Service: `{key}`**\n'
        text += f'- Button text: `{button_text}`\n'
        text += f'- Description: `{description}`\n'
        text += f'- Password: `{password}`\n'
        text += f'- Style: `{style}`\n'
        text += f'- Emoji: {emoji}\n'
        await ctx.send(text)

  @password_config.command(name="add_service")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_add_service(self, ctx: commands.Context, service_name: str) -> None:
    """Adds a new service."""
    success = False
    async with self.config.services() as services:
      if service_name not in services:
        services[service_name] = {
          'button_text': service_name,
          'description': 'Password',
          'password': "",
          'style': 'primary',
          'emoji': None,
        }
        await ctx.send(f'Service `{service_name}` added.')
        success = True
      else:
        await ctx.send(f'Service `{service_name}` already exists.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="remove_service")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_remove_service(self, ctx: commands.Context, service_name: str) -> None:
    """Removes an existing service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        del services[service_name]
        await ctx.send(f'Service `{service_name}` removed.')
        success = True
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="set_button_text")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_button_text(self, ctx: commands.Context, service_name: str, *, button_text: str) -> None:
    """Sets the button text for the given service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        service = services[service_name]
        service['button_text'] = button_text
        services[service_name] = service

        await ctx.send(f'Button text for service `{service_name}` set to: {button_text}.')
        success = True
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="set_description")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_description(self, ctx: commands.Context, service_name: str, *, description: str) -> None:
    """Sets the description for the given service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        service = services[service_name]
        service['description'] = description
        services[service_name] = service

        await ctx.send(f'Description for service `{service_name}` set to: {description}.')
        success = True
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="set_style")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_style(self, ctx: commands.Context, service_name: str, *, style: str) -> None:
    """Sets the button style for the given service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        valid_styles = [
            i for i in dir(ButtonStyle) if not i.startswith("_") and i != "try_value"
        ]

        if style.lower() in valid_styles:
          service = services[service_name]
          service['style'] = style
          services[service_name] = service

          await ctx.send(f'Style for service `{service_name}` set to: {style}.')
          success = True
        else:
          style_list = humanize_list(valid_styles)
          await ctx.send(f'Error: `{style}` is not a valid style. Choose from: `{style_list}`')
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="set_emoji")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_emoji(self, ctx: commands.Context, service_name: str, *, emoji: str = None) -> None:
    """Sets the optional emoji for the given service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        service = services[service_name]

        try:
          if emoji is None:
            service['emoji'] = None
            await ctx.send(f'Emoji for service `{service_name}` cleared.')
          else:
            # Check that this is a valid emoji, throw exception if it is not
            PartialEmoji.from_str(emoji)
            service['emoji'] = emoji
            await ctx.send(f'Emoji for service `{service_name}` set to: {emoji}.')

          services[service_name] = service
          success = True
        except HTTPException:
          await ctx.send(f'Error: {emoji} is not a valid emoji.')
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="set_password")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_password(self, ctx: commands.Context, service_name: str, password: str) -> None:
    """Sets the password for the given service."""
    success = False
    async with self.config.services() as services:
      if service_name in services:
        service = services[service_name]
        service['password'] = password
        services[service_name] = service

        await ctx.send(f'Password for service `{service_name}` set.')
        success = True
      else:
        await ctx.send(f'Service `{service_name}` does not exist.')
    if success:
      await self.password_config_update(ctx)

  @password_config.command(name="update")
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_update(self, ctx: commands.Context) -> None:
    """Updates the message after configuring other settings."""
    message_channel_id = await self.config.message_channel_id()
    message_id = await self.config.message_id()
    message_text = await self.config.message_text()
    log_channel_id = await self.config.log_channel_id()
    response_lifespan = await self.config.response_lifespan()

    if message_channel_id is None:
      await ctx.send('Password message channel has not been set. Run `[p]password_config set_message_channel` to set it.')
      return

    log_channel: TextChannel = None
    if log_channel_id is not None:
      log_channel = self.bot.get_channel(log_channel_id)

    message_channel = self.bot.get_channel(message_channel_id)

    view = PasswordView(self.config, log_channel, response_lifespan)
    await view.createButtons()

    # If the button message id has not been stored in the cog, create a new message
    if message_id is None:
      await self.create_button_message(ctx, message_channel, view, message_text)
      return

    try:
      message = await message_channel.fetch_message(message_id)

    # If the button message does not exist in Discord, create a new message
    except NotFound:
      await ctx.send(f'Password message does not exist, recreating...')
      await self.create_button_message(ctx, message_channel, view, message_text)
      return

    # Otherwise, edit the existing message
    await message.edit(content = message_text, view = view)
    await ctx.send(f'Password message updated: {message.jump_url}.', suppress_embeds = True)

  async def create_button_message(self, ctx: commands.Context, channel: TextChannel, view: View, message_text: str):
    message = await channel.send(message_text, view = view)
    await self.config.message_id.set(message.id)
    await ctx.send(f'Message created: {message.jump_url}.', suppress_embeds = True)