from commands.bot_instance import StarlowBot
from random import choice
from os import getenv
import hikari

bot = StarlowBot(getenv("TOKEN"))


@bot.listen()
async def load_commands(event: hikari.StartedEvent) -> None:
    app = await bot.rest.fetch_application()
    await bot.rest.set_application_commands(
        app.id,
        bot.build_commands()
    )

try:
    games = ["Super Mario RPG: Legend of the Seven Stars",
             "Paper Mario",
             "Mario & Luigi: Superstar Saga",
             "Paper Mario: The Thousand-Year Door",
             "Mario & Luigi: Partners in Time",
             "Super Paper Mario",
             "Mario & Luigi: Bowser's Inside Story",
             "Paper Mario: Sticker Star",
             "Mario & Luigi: Dream Team",
             "Mario & Luigi: Paper Jam",
             "Paper Mario: Color Splash",
             "Minion Quest: The Search for Bowser",
             "Mario + Rabbids: Kingdom Battle",
             "Bowser Jr.'s Journey",
             "Paper Mario: The Origami King",
             "Mario + Rabbids: Sparks of Hope",
             "Mario & Luigi: Brothership"
             ]
    activity = hikari.Activity(name=choice(games))
    bot.run(activity=activity)
except hikari.HikariInterrupt:
    pass
