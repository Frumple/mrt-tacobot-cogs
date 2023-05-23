from discord import Reaction, User
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.mod import is_mod_or_superior

class DynmapEvents:
  def __init__(self):
    self.bot: Red
    self.config: Config

  # Event handler when a user adds a reaction
  @commands.Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
    # Is the reaction a "stop button"?
    if reaction.emoji == self.UNICODE_STOP_BUTTON:
      async with self.config.render_queue() as render_queue:

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
