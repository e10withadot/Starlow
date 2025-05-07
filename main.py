from commands.bot_instance import StarlowBot
import hikari

bot = StarlowBot("[YOUR TOKEN HERE]")


@bot.listen()
async def load_commands(event: hikari.StartedEvent) -> None:
    app = await bot.rest.fetch_application()
    await bot.rest.set_application_commands(
        app.id,
        bot.build_commands()
    )

try:
    bot.run()
except hikari.HikariInterrupt:
    pass
