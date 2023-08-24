import re
import os
import json
import miru
import asyncio
import sql_tools
import config as c
import interface.views as views
import interface.gen_comp as comp
from hikari import ButtonStyle, MessageFlag, TextInputStyle

# Battle Editor Panels
# phase editor panel
class PhasePanel(views.Panel):
	def __init__(self):
		super().__init__(obj= c.save["phases"],
		components= [
		SpawnEnemies(),
		comp.DelButton(),
		Advanced()
		])
	
	def onEdit(self):
		if len(c.save["phases"]) > 1:
			self.embeds= []
			for i in range(len(c.save["phases"])-1):
				conditions= c.save["phases"]["names"][i]
				results= c.save["phases"][i]
				self.embeds.append(c.StEmbed(title=conditions, description=results))
						
		elif len(c.save["enemies"]) > 1:
			self.embeds= c.StEmbed(title="An empty battle is a sad one.", description="Spawn enemies into battle with the button below.")
		else:
			self.embeds= c.StEmbed(title="An empty battle is a sad one.", description="Add enemies to the enemy list, then return to spawn them to the battlefield.")

# enemy editor panel
class EnemyPanel(views.Panel):
	def __init__(self):
		obj= c.save["enemies"]
		super().__init__(obj= obj,
		components= [
		comp.AddButton(template= {"HP": 5, "POW": 1, "DEF": 0, "SPEED": 0, "STACHE": 0, "spiny": False, "flying": False, "moves": {"names":[]}},
		title= "New Enemy"
		),
		comp.UIEdit(
		items= [
		comp.NameButton(),
		comp.StatButton(),
		ToggleSpiny(),
		ToggleFlying()
		]),
		comp.DupButton(),
		comp.DelButton(),
		Moves()
		])
	
	def onEdit(self):
		enemies = c.save["enemies"]
		if len(enemies) > 1:
			self.embeds = []
			for i in range(len(enemies)-1):
				name= enemies["names"][i]
				enemy= enemies[i]
				info= f"HP: {enemy.get('HP')}\nPOW: {enemy.get('POW')}\nDEF: {enemy.get('DEF')}\nSpeed: {enemy.get('SPEED')}\nStache: {enemy.get('STACHE')}\nSpiny: {enemy.get('spiny')}\nFlying: {enemy.get('flying')}"
				self.embeds.append(c.StEmbed(title= name, description= info))
		else:
			self.embeds= c.StEmbed(title="No enemies.", description="Add an enemy with the button below.")
	
# character editor panel
class CharPanel(views.Panel):
	def __init__(self):
		inputs=[
			miru.TextInput(label="Name", placeholder="Input name.", required=True, max_length=30),
			miru.TextInput(label="Icon URL", placeholder="Input icon URL.", required=True, max_length=100)
		]
		super().__init__(obj= c.save["dialogue"]["chars"],
		components= [
		comp.AddButton(
		title= "Add Character",
		inputs= inputs
		),
		comp.ValueEdit(
		keys= ["/r", "/n"],
		title= "Edit Character",
		inputs= inputs
		),
		comp.DupButton(),
		comp.DelButton(),
		Dialogue()
		])
	
	def onEdit(self):
		chars= c.save["dialogue"]["chars"]
		if len(chars) > 1:
			self.embeds= []
			for i in range(len(chars)-1):
				name= chars["names"][i]
				url= chars[i]
				nEmbed= c.StEmbed(title= name)
				nEmbed.set_thumbnail(url)
				self.embeds.append(nEmbed)
		else:
			self.embeds= c.StEmbed(title="No characters.", description="Add a character to use for dialogue events!")
			
# dialogue event editor panel
class EventPanel(views.Panel):
	def __init__(self):
		inputs= [miru.TextInput(label="Dialogue Event", placeholder='[Character No.]:[Dialogue] (separate by new lines).', style=TextInputStyle.PARAGRAPH, required=True, max_length=500), ]
		super().__init__(obj= c.save["dialogue"]["events"],
		components= [
		EventMod(),
		EventMod(edit= True),
		DupEvent(),
		DelEvent(),
		Chars()
		])
	
	def onEdit(self):
		# set events list
		events= c.save["dialogue"]["events"]
		if events:
			# set embeds
			self.embeds= []
			# for each event in list
			for event in events:
				# set embeds for one message
				dEmbeds= []
				# for each name
				for i, content in event:
					name= c.save["dialogue"]["chars"]["names"][int(i)-1]
					url= c.save["dialogue"]["chars"][int(i)-1]
					if url:
						# create new embed
						nEmbed= c.StEmbed(title= name, description= f'"{content}"')
						nEmbed.set_thumbnail(url)
						dEmbeds.append(nEmbed)
				# append to embeds
				self.embeds.append(dEmbeds)
		else:
			self.embeds= c.StEmbed(title="No events.", description="Create a dialogue event below!")

# Battle Editor Components
# condition add button: calls modal
class SpawnEnemies(comp.UIEdit):
	def __init__(self):
		super().__init__(
		items= [
		EnemySelect(),
		DelSpawn(),
		ClearSpawn()
		],
		label="Spawn Enemies",
		row=1
		)
	
	def onChange(self):
		if len(c.save["enemies"]) > 1:
			self.disabled= False
		else:
			self.disabled= True

# updating og phase view components
async def phaseComp(og: miru.View, view: miru.View, ctx: miru.ViewContext):
	# updating UIEdit components
	for i in [1,2]:
		view.children[i].onChange()
	await ctx.edit_response(components= view)
	for child in og.children:
		if child.__class__.__name__ in ["SpawnEnemies", "comp.ValueEdit", "comp.DupButton" ,"comp.DelButton"]:
			child.onChange()
	await og.message.edit(components=og)

# enemy selection
class EnemySelect(miru.TextSelect):
	def __init__(self):
		super().__init__(
		options= [miru.SelectOption(label= "n/a")],
		placeholder= "Add Enemies",
		disabled= True
		)
		
	def onChange(self):
		if c.save["enemies"]["names"]:
			self.disabled= False
			options= []
			for i, enemy in enumerate(c.save["enemies"]["names"]):
				options.append(
				miru.SelectOption(label= enemy, value= str(i))
				)
		else:
			self.disabled= True
		self.options= options
	
	async def callback(self, ctx: miru.ViewContext):
		# set up modal
		self.is_default= False
		modal= comp.GenModal(title="Number of Enemies")
		modal.add_item(miru.TextInput(label= "Number", placeholder= "Input amount of enemies.", required= True, max_length= 1))
		await ctx.respond_with_modal(modal)
		await modal.wait()
		# outputting spawn syntax
		spawn= f"spawn:{int(self.values[0])+1},{list(modal.values)[0].value}"
		if hasattr(self.view, "num"):
			out= "&" + spawn
			c.save["phases"][self.view.num]+= out
		else:
			if len(c.save["phases"]) > 1:
				out= "e0:0hp"
				self.view.num= self.view.page+1
			else:
				out= "start"
				self.view.num= 0
			c.save["phases"]["names"].append(out)
			c.save["phases"][self.view.num]= spawn
		# updating root embed and components
		await views.updateEmbed(self.view.og)
		await phaseComp(self.view.og, self.view, ctx)

# delete recent spawn
class DelSpawn(comp.DelButton):
	def __init__(self):
		super().__init__()
		self.label= "Delete Recent"
		
	def onChange(self):
		if hasattr(self.view, "num"):
			self.disabled= False
		else:
			self.disabled= True
		
	async def callback(self, ctx: miru.ViewContext):
		c.save["phases"][self.view.num]= re.sub(r"&(?!.*&).+$", "", c.save["phases"][self.view.num])
		if not c.save["phases"][self.view.num]:
			c.save["phases"].pop(self.view.num)
			c.save["phases"]["names"].pop(self.view.num)
			delattr(self.view, "num")
			await phaseComp(self.view.og, self.view, ctx)
		if self.view.page == len(self.view.og.pages):
			self.view.og.page-=1
		await views.updateEmbed(self.view.og)

# clear all spawns
class ClearSpawn(miru.Button):
	def __init__(self):
		super().__init__(
		label= "Clear",
		style= ButtonStyle.SECONDARY,
		emoji=chr(0x1F6AB)
		)
	
	def onChange(self):
		if hasattr(self.view, "num"):
			self.disabled= False
		else:
			self.disabled= True
			
	async def callback(self, ctx: miru.ViewContext):
		c.save["phases"].pop(self.view.num)
		c.save["phases"]["names"].pop(self.view.num)
		delattr(self.view, "num")
		await phaseComp(self.view.og, self.view, ctx)
		if self.view.page == len(self.view.og.pages):
			self.view.og.page-=1
		await views.updateEmbed(self.view.og)

# advanced options button
class Advanced(comp.SwitchButton):
	def __init__(self):
		super().__init__(
		emojis=[chr(0x1F53D), chr(0x1F53C)],
		row=1
		)
		
	def onChange(self):
		if self.index is None:
			self.index= 0
		super().onChange()
		
	async def callback(self, ctx: miru.ViewContext):
		inputs=[
			miru.TextInput(label="If", placeholder="Input condition.", required=True, max_length=50),
			miru.TextInput(label="Then", placeholder="Input resulting event.", required=True, max_length=100)
		]
		items=[
			comp.AddButton(inputs= inputs,
			title= "Add Condition",
			),
			comp.ValueEdit(inputs= inputs,
			keys=["/r", "/n"],
			title= "Set Condition"
			),
			comp.DupButton()
		]
		super().callback(ctx)
		if self.emoji == chr(0x1F53D):
			for item in items:
				item.row= 2
				self.view.panels[self.view.now].comp.append(item)
		else:
			for i in [5,4,3]:
				self.view.panels[self.view.now].comp.pop()
		await self.view.swapView(ctx, int(self.view.now))
		await views.updateComp(self.view, ctx, 2)
		
# Spiny Toggle
class ToggleSpiny(comp.SwitchButton):
	def __init__(self):
		super().__init__(
		emojis= [chr(0x1F534), chr(0x1F7E2)],
		label= "Spiny",
		row=2
		)
		
	def onChange(self):
		if not c.save.get("enemies"):
			self.disabled = True
			return
		self.disabled = False
		# determine index
		if self.index is None:
			if c.save["enemies"][self.view.page]["spiny"]:
				self.index= 1
			else:
				self.index= 0
		super().onChange()

	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		if self.index == 1:
			c.save["enemies"][self.view.page]["spiny"] = True
		else:
			c.save["enemies"][self.view.page]["spiny"] = False
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 2)

# Flying Toggle
class ToggleFlying(comp.SwitchButton):
	def __init__(self):
		super().__init__(
		emojis= [chr(0x1F534), chr(0x1F7E2)],
		label= "Flying",
		row=2
		)
		
	def onChange(self):
		if not c.save.get("enemies"):
			self.disabled = True
			return
		self.disabled = False
		if self.index is None:
			if c.save["enemies"][self.view.page]["flying"]:
				self.index= 1
			else:
				self.index= 0
		super().onChange()

	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		if self.index == 1:
			c.save["enemies"][self.view.page]["flying"] = True
		else:
			c.save["enemies"][self.view.page]["flying"] = False
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 3)

# to moves menu
class Moves(miru.Button):
	def __init__(self):
		super().__init__(
		label="Moves >",
		row=2
		)
		
	def onChange(self):
		if len(c.save["enemies"]) > 1:
			self.disabled = False
		else:
			self.disabled = True
	
	async def callback(self, ctx: miru.ViewContext):
		# set move panel
		self.view.panels[self.view.now]= comp.MovePanel(self.view.page)
		# add back button
		self.view.panels[self.view.now].comp.append(Back())
		# swap view
		await self.view.swapView(ctx, int(self.view.now))
		
# back to enemy view
class Back(miru.Button):
	def __init__(self):
		super().__init__(
		label="< Back",
		row=2
		)
		
	async def callback(self, ctx: miru.ViewContext):
		# reset moves var
		c.moves={}
		# set enemy view items
		self.view.panels[self.view.now]= EnemyPanel()
		# swap view
		await self.view.swapView(ctx, int(self.view.now))
		
# to dialogue menu
class Dialogue(miru.Button):
	def __init__(self):
		super().__init__(
		label="Dialogue >",
		row=2
		)
	
	def onChange(self):
		if len(c.save["dialogue"]["chars"]) > 1:
			self.disabled = False
		else:
			self.disabled = True
		
	async def callback(self, ctx: miru.ViewContext):
		# set event panel
		self.view.panels[self.view.now]= EventPanel()
		# swap view
		await self.view.swapView(ctx, int(self.view.now))

# event addition/edit modal
class EventMod(comp.ModalButton):
	def __init__(self, edit: bool= False):
		self.edit= edit
		if self.edit:
			emoji= chr(0x270F)
			style= ButtonStyle.SECONDARY
			title= "Edit Event"
		else:
			emoji= chr(0x2795)
			style= ButtonStyle.SUCCESS
			title= "Add Event"
		super().__init__(inputs= [miru.TextInput(label="Dialogue Event", placeholder='[Character No.]:[Dialogue] (separate by new lines).', style=TextInputStyle.PARAGRAPH, required=True, max_length=500), ],
		title= title,
		emoji= emoji,
		style= style,
		row= 1
		)
		
	def refresh(self):
		if self.edit:
			value=""
			# array to modifiable input
			for event in c.save["dialogue"]["events"][self.view.page]:
				value += f"{event[0]}:{event[1]}\n"
		else:
			value= None
		self.modal.children[0].value= value
	
	def onChange(self):
		if len(c.save["dialogue"]["events"]) > 0:
			self.disabled = False
		elif self.edit:
			self.disabled = True
	
	async def callback(self, ctx: miru.ModalContext) -> None:
		await super().callback(ctx)
		# get event info
		event= list(self.modal.values)[0].value
		arr = []
		# insert into array
		for dialogue in event.split("\n"):
			arr.append(dialogue.split(":"))
		# if edit
		if self.edit:
			c.save["dialogue"]["events"][self.view.page] = arr
		else:
			c.save["dialogue"]["events"].append(arr)
			await views.updateComp(self.view, ctx, range(1, 4))
		await views.updateEmbed(self.view)
		
# duplicate event button
class DupEvent(comp.DupButton):
	def onChange(self):
		if c.save["dialogue"]["events"]:
			self.disabled = False
		else:
			self.disabled = True
	
	async def callback(self, ctx: miru.ViewContext):
		# save to new event
		c.save["dialogue"]["events"].append(c.save["dialogue"]["events"][self.view.page])
		await views.updateEmbed(self.view)
		
class DelEvent(comp.DelButton):
	def onChange(self):
		if c.save["dialogue"]["events"]:
			self.disabled = False
		else:
			self.disabled = True
	
	async def callback(self, ctx: miru.ViewContext):
		# save to new event
		c.save["dialogue"]["events"].pop(self.view.page)
		
		if self.view.page == len(self.view.pages)-1:
			self.view.page-=1
			
		await views.updateComp(self.view, ctx, range(1, 4))
		await views.updateEmbed(self.view)
		
# to character menu
class Chars(miru.Button):
	def __init__(self):
		super().__init__(
		label="< Characters",
		row=2
		)
		
	async def callback(self, ctx: miru.ViewContext):
		# set character panel
		self.view.panels[self.view.now]= CharPanel()
		# swap view
		await self.view.swapView(ctx, int(self.view.now))

# add battle to Starlow button		
class StAdd(miru.Button):
	def __init__(self):
		super().__init__(emoji=chr(0x2B50), label="Save to Starlow", row=4)
		
	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = views.ConfirmView(ctx)
		msg= await ctx.respond(content="Would you like to add this battle to Starlow?", components=view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			battles= sql_tools.loadID(self.view.guild, False)
			for i, battle in enumerate(battles):
				if not battle:
					# save
					sql_tools.saveID(self.view.guild, c.save, False, i)
					self.view.output= True
					await ctx.edit_response(content= "Saved.", components= None)
					break
				elif i == 4:
					self.view.output= False
					await ctx.edit_response(content= "Max battle capacity reached (5 per server). Battle not saved.", components= None)
			# edit confirmation and delete og
			await self.view.message.delete()
			self.view.stop()

# export battle to .json
class JsonExport(miru.Button):
	def __init__(self):
		super().__init__(label="Export .json", row=4, style=ButtonStyle.SECONDARY)

	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = views.ConfirmView(ctx)
		msg= await ctx.respond(content="Would you like to export this battle as .json?", components=view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			path= os.path.abspath(__file__).replace("btl_comp.py", "btl.json")
			with open(path, "x") as file:
				file.write(json.dumps(c.save))
			try:
				await asyncio.wait_for(await ctx.respond(attachment= path), timeout=10)
			except Exception as e:
				await ctx.edit_response(content= f"Upload failed. ({e})", components= None)
			os.remove(path)
			# edit confirmation and delete og
			await ctx.edit_response(content= "Done.", components= None)
			await self.view.message.delete()
			self.view.stop()