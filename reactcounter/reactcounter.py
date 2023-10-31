from datetime import datetime
from dateutil.parser import ParserError, parse
from dateutil.tz import tzutc
from discord import ForumChannel, Message, Thread
from redbot.core import app_commands, commands, checks
from redbot.core.bot import Red

async def get_thread_starter_message(thread: Thread) -> Message:
  if thread.starter_message is not None:
    return thread.starter_message

  async for message in thread.history(limit = 1, oldest_first = True):
    return message

class DateConverter(commands.Converter):
  async def convert(self, ctx: commands.Context, input: str) -> datetime:
    try:
      output = parse(input, default=datetime.now(), ignoretz=True, yearfirst=True).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=tzutc()
      )

      return output
    except ParserError:
      if ctx.interaction:
        raise commands.BadArgument("Invalid date. Example in YYYY-MM-DD format: `2000-01-29`.")
      raise commands.BadArgument(f"Invalid date. See {ctx.clean_prefix}help {ctx.command.qualified_name} for more information.")

class ReactCounter(commands.Cog):
  """Utility commands for counting reactions in channels."""

  def __init__(self, bot: Red):
    self.bot = bot

  @commands.hybrid_group(name='reactcounter')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def reactcounter(self, ctx: commands.Context) -> None:
    """Commands for counting reactions."""
    if ctx.invoked_subcommand is None:
      pass

  @reactcounter.command(name='count')
  @checks.admin_or_permissions()
  @app_commands.default_permissions(administrator=True)
  @app_commands.checks.has_permissions(administrator=True)
  async def count(self, ctx: commands.Context, channel: ForumChannel, startDate: DateConverter, endDate: DateConverter):
    """
    Counts the number of reactions per player made on closed topics in a forum channel within a specified date range.

    Start date and end date should be in YYYY-MM-DD format.
    Example: January 29, 2000 = `2000-01-29`

    Start date and end date are assumed to be 00:00 UTC time.
    Therefore, if you want a date range for the entirety of a month, use start and end dates like this:
    - Start date: `2000-01-01` (counts reactions after January 1, 2000 00:00 UTC)
    - End date: `2000-02-01` (counts reactions before February 1, 2000 00:00 UTC)
    """
    await ctx.send("Processing, please wait...")

    user_reaction_counts = {}
    text = f'**Reaction counts in {channel.mention} from {startDate} to {endDate}:**\n\n'

    threads = [thread async for thread in channel.archived_threads(before = endDate)]
    for thread in threads:
      if thread.archive_timestamp < startDate:
        continue

      print(thread.name, flush=True)

      starter_message = await get_thread_starter_message(thread)
      if starter_message is None:
        continue

      for reaction in starter_message.reactions:
        users = [user async for user in reaction.users()]
        for user in users:
          username = user.display_name
          print(f'- {username}', flush=True)
          user_reaction_counts[username] = user_reaction_counts.get(username, 0) + 1

    for key, value in user_reaction_counts.items():
      text += f'- {key}: {value}\n'

    await ctx.send(text)
