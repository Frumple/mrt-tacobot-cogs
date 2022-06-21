from redbot.core import Config, commands, checks
from discord.errors import Forbidden

class Password(commands.Cog):
  """Allows users to obtain access passwords for external services."""

  def __init__(self):
    default_guild = {
      'entries': {}
    }
    self.config = Config.get_conf(self, identifier=8373008181, force_registration=True)
    self.config.register_guild(**default_guild)

  @commands.group()
  async def password(self, ctx: commands.Context):
    if ctx.invoked_subcommand is None:
      pass

  @password.command(name="set")
  @checks.admin_or_permissions()
  async def password_set(self, ctx, name: str, *, value: str):
    """Sets the password for a given service."""
    async with self.config.guild(ctx.guild).entries() as entries:
      entries[name] = value
      await ctx.send(f'Password for `{name}` has been set.');

  @password.command(name="clear")
  @checks.admin_or_permissions()
  async def password_clear(self, ctx, name: str):
    """Clears the password for a given service."""
    async with self.config.guild(ctx.guild).entries() as entries:
      if name in entries:
        del entries[name]
        await ctx.send(f'Password for `{name}` has been cleared.')
      else:
        await ctx.send(f'No password exists for `{name}`.')

  @password.command(name="get")
  async def password_get(self, ctx, name: str):
    """Sends the requested password to the user via DM."""
    async with self.config.guild(ctx.guild).entries() as entries:
      if name in entries:
        await ctx.send(f'{ctx.author.mention} has requested the password for `{name}`.')
        try:
          await ctx.author.send(entries[name])
        except Forbidden:
          await ctx.send('Error: Unable to send password via direct message.')
          await ctx.send('In your Privacy Settings for this Discord server, please make sure to "Allow direct messages from server members", and then try requesting the password again.')
      else:
        await ctx.send(f'No password exists for `{name}`.')

  @password.command(name="list")
  async def password_list(self, ctx):
    """Lists the names of all available passwords."""
    async with self.config.guild(ctx.guild).entries() as entries:
      names = [*entries]
      await ctx.send(f'Available passwords: {names}')
