from discord import ButtonStyle, Interaction, TextChannel
from discord.errors import NotFound
from discord.ui import Button, View
from redbot.core import Config, app_commands, commands, checks
from redbot.core.bot import Red

class PasswordButton(Button):
  def __init__(self, service_name: str, service: dict, log_channel: TextChannel = None):
    super().__init__(
      style = ButtonStyle.primary,
      label = service['button_text']
    )
    self.service_name = service_name
    self.service = service
    self.log_channel = log_channel

  async def callback(self, interaction: Interaction):
    description = self.service['description']
    password = self.service['password']
    text = f'{description}: `{password}`'

    # If log channel is defined, record the password retrieval to it
    if self.log_channel is not None:
      await self.log_channel.send(f'{interaction.user.mention} has requested the password for `{self.service_name}`.')

    # Send the password only to the user
    await interaction.response.send_message(text, ephemeral = True)

class PasswordView(View):
  def __init__(self, config: Config, log_channel: TextChannel = None):
    super().__init__(
      timeout = None
    )
    self.config = config
    self.log_channel = log_channel

  async def createButtons(self):
    self.clear_items()
    async with self.config.services() as services:
      for service_name, service in services.items():
        button = PasswordButton(service_name, service, self.log_channel)
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
    await ctx.send(f'Message channel has been set to: {channel.mention}')
    await self.password_config_update(ctx)

  @password_config.command(name='set_message_text')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_message_text(self, ctx: commands.Context, *, message_text: str) -> None:
    """Sets the text of the message."""
    await self.config.message_text.set(message_text)
    await ctx.send(f'Message text has been set to: {message_text}')
    await self.password_config_update(ctx)

  @password_config.command(name='set_log_channel')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def password_config_set_log_channel(self, ctx: commands.Context, channel: TextChannel = None) -> None:
    """Sets the channel that logs all password retrievals (optional)."""
    if channel is None:
      await self.config.log_channel_id.clear()
      await ctx.send('Log channel cleared.')
    else:
      await self.config.log_channel_id.set(channel.id)
      await ctx.send(f'Log channel has been set to: {channel.mention}')
    await self.password_config_update(ctx)

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
          'password': ""
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
        services[service_name] = {
          'button_text': button_text,
          'description': services[service_name]['description'],
          'password': services[service_name]['password']
        }
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
        services[service_name] = {
          'button_text': services[service_name]['button_text'],
          'description': description,
          'password': services[service_name]['password']
        }
        await ctx.send(f'Description for service `{service_name}` set to: {description}.')
        success = True
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
        services[service_name] = {
          'button_text': services[service_name]['button_text'],
          'description': services[service_name]['description'],
          'password': password
        }
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

    if message_channel_id is None:
      await ctx.send('Message channel has not been set. Run `[p]password_config set_message_channel` to set it.')
      return

    log_channel: TextChannel = None
    if log_channel_id is not None:
      log_channel = self.bot.get_channel(log_channel_id)

    message_channel = self.bot.get_channel(message_channel_id)

    view = PasswordView(self.config, log_channel)
    await view.createButtons()

    # If the button message id has not been stored in the cog, create a new message
    if message_id is None:
      await self.create_button_message(ctx, message_channel, view, message_text)
      return

    try:
      message = await message_channel.fetch_message(message_id)

    # If the button message does not exist in Discord, create a new message
    except NotFound:
      await ctx.send(f'Message does not exist, recreating...')
      await self.create_button_message(ctx, message_channel, view, message_text)
      return

    # Otherwise, edit the existing message
    await message.edit(content = message_text, view = view)
    await ctx.send(f'Message updated: {message.jump_url}.', suppress_embeds = True)

  async def create_button_message(self, ctx: commands.Context, channel: TextChannel, view: View, message_text: str):
    message = await channel.send(message_text, view = view)
    await self.config.message_id.set(message.id)
    await ctx.send(f'Message created: {message.jump_url}.', suppress_embeds = True)