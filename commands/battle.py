import lightbulb
import re
import os
import time
import sql_tools
import config as c
from slipper import jsonStr
from hikari import OptionType, MessageFlag, Permissions
from miru import SelectOption
import btl_logic as btl
import interface.views as views
import interface.btl_comp as btlc

plugin = lightbulb.Plugin("battle")

@plugin.command
@lightbulb.command("battle", "Create, edit, and export battles.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def battle(ctx: lightbulb.Context):
	pass

# battle editor initalization
async def btl_editor(ctx: lightbulb.Context):
	# system buttons
	sys=[
		btlc.JsonExport(),
		views.QuitButton()
		]
	if hasattr(ctx.options, "battle"):
		# get battle slot
		i= int(re.findall(r'\d+', ctx.options.battle)[0])-1
		btl_save= sql_tools.loadID(ctx.guild_id, False)[i]
		if not btl_save:
			await ctx.respond(content= "That slot is empty. Use `/battle create` to add a new battle instead.", flags= MessageFlag.EPHEMERAL)
			return
		c.save= btl_save
		sys.insert(0, views.SaveButton())
	else:
		i= None
		c.save= {"phases":{"names":[]}, "enemies":{"names":[]}, "dialogue":{"chars":{"names":[]}, "events":[]}}
		sys.insert(0, btlc.StAdd())
	c.enemy= True
	# battle editor options
	options=[
		SelectOption(label="Order of Events", description="Set the order of battle events, and their conditions.", emoji= chr(0x26F3), is_default= True),
		SelectOption(label="Enemy List", description="Edit enemies and their moves.", emoji= chr(0x1F9CC)),
		SelectOption(label="Add Dialogue", description="Add mid-battle dialogue.", emoji= chr(0x1F4AC))
		]
	# Editor panels
	panels= [
		btlc.PhasePanel(),
		btlc.EnemyPanel(),
		btlc.CharPanel()
		]
	# current command user
	user= ctx.author
	view= views.MainView(user, panels, options, sys)
	# battle slot no. (only on edit)
	view.choice= i
	if isinstance(view.pages, list):
		embed1= view.pages[0]
	else:
		embed1= view.pages
	message= await ctx.respond(embed=embed1, components=view)
	# Starts UI View with the embed
	await view.start(message)
	await view.wait()

@battle.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(Permissions.MANAGE_CHANNELS))
@lightbulb.command("create", "Create a new battle.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create(ctx: lightbulb.Context):
	await btl_editor(ctx)

@battle.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(Permissions.MANAGE_CHANNELS))
@lightbulb.option("battle", "The battle you want to edit.", required= True, choices= ["Slot 1", "Slot 2", "Slot 3", "Slot 4", "Slot 5"])
@lightbulb.command("edit", "Edit an existing battle.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def edit(ctx: lightbulb.Context):
	await btl_editor(ctx)

@battle.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(Permissions.MANAGE_CHANNELS))
@lightbulb.option("battle", "A battle saved in Starlow.", choices= ["Slot 1", "Slot 2", "Slot 3", "Slot 4", "Slot 5"], required= False)
@lightbulb.option("file", "A Starlow-supported .json file.", type= OptionType.ATTACHMENT, required= False)
@lightbulb.command("start", "Start a battle.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def start(ctx: lightbulb.Context):
	if ctx.options.battle or ctx.options.file:
		c.save= []
		# check for input
		if ctx.options.battle:
			# get slot index
			i= int(re.findall(r'\d+', ctx.options.battle)[0])-1
			# get battle from slot
			c.battle= sql_tools.loadID(ctx.guild_id, False)[i]
		elif ctx.options.file:
			# read file
			async with ctx.options.file.stream() as f:
				data= await f.read()
			c.battle = jsonStr(data.decode("utf-8"))
		# get settings
		c.save= sql_tools.loadID(ctx.guild_id)
		# get special moves data
		path= os.path.abspath(__file__).replace(r"\commands\battle.py", r"\templates\special.json")
		with open(path) as f:
			c.moves= jsonStr(f.read())
		# add custom moves to c.moves
		if c.save["moves"].get("names"):
			for j, name in enumerate(c.save["moves"]["names"]):
				c.moves["names"].append(name)
				num= j+len(c.save["moves"]["names"])-1
				c.moves[num]= c.save["moves"][j]
		# get battle channel
		c.channel= await ctx.app.rest.fetch_channel(c.save["channel"])
		await ctx.respond(content= f"The battle is now starting in {c.channel.mention}!", flags= MessageFlag.EPHEMERAL)
		# set member acquisition message
		embed= (
			c.StEmbed(title="React to join!", description="If you want to join the battle, react to this message now!")
			.set_footer("The battle will start in 1 minute!")
		)
		msg= await c.channel.send(embed= embed)
		await ctx.app.rest.add_reaction(message= msg, channel= c.channel, emoji= "🟡")
		# wait a minute for registration
		time.sleep(60)
		# update message info
		msg= await c.channel.fetch_message(msg)
		c.members= msg.reactions[0].count-1
		await btl.turn_order(ctx)
	else:
		await ctx.respond(content= "Please select a battle from either your files or Starlow's database.", flags= MessageFlag.EPHEMERAL)

def load(bot):
	bot.add_plugin(plugin)

def unload(bot):
	bot.remove_plugin(plugin)