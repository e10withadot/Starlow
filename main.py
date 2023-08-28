import lightbulb
import miru
import time

bot = lightbulb.BotApp(token="[insert token here]")
miru.install(bot)

@bot.command
@lightbulb.command("ping", "Check if bot is online.")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
	# checks if bot is online, basically ping
	await ctx.respond(f"Pong!\nElapsed Time: {time.process_time()}s")

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("extension", "The extension to reload.", required= True, choices= bot.extensions)
@lightbulb.command("reload", "[BOT ADMIN] Reload a Starlow extension.", ephemeral= True)
@lightbulb.implements(lightbulb.SlashCommand)
async def reload(ctx: lightbulb.Context) -> None:
	bot.reload_extensions(ctx.options.extension)
	await ctx.respond(content= f"Reloaded {ctx.options.extension}.")

bot.load_extensions("commands.luigi")
bot.load_extensions("commands.settings")
bot.load_extensions("commands.battle")

# Run the bot
bot.run()
