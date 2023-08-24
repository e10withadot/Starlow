import miru
import config as c
import interface.views as views
from copy import deepcopy
from hikari import ButtonStyle, MessageFlag, Emoji

# bunch of generic components used across the program

# SwitchButton switches between a list of options
class SwitchButton(miru.Button):
	def __init__(self, emojis: Emoji, options = None, **kwargs):
		super().__init__(style= ButtonStyle.SECONDARY, **kwargs)
		self.options = options
		if self.options:
			self.label = self.options[0]
		self.emojis = emojis
		self.emoji = self.emojis[0]
		self.index = None
		
	def onChange(self):
		if self.index is None and self.options:
			for i, option in enumerate(self.options):
				if option == self.label:
					self.index= i
					break
		if self.options:
			self.label = self.options[self.index]
		self.emoji = self.emojis[self.index]
		
	def callback(self, ctx: miru.ViewContext):
		for i, emoji in enumerate(self.emojis):
			if self.emoji == emoji:
				if i+1 <= len(self.emojis)-1:
					self.index = i+1
				else:
					self.index = 0
				break

# modal call button
class ModalButton(miru.Button):
	def __init__(self, inputs, title: str, **kwargs):
		self.inputs= inputs
		self.title= title
		super().__init__(**kwargs)
	
	def refresh(self):
		pass
	
	# onChange affects button availability
	def onChange(self):
		if len(self.view.obj) > 1:
			self.disabled = False
		else:
			self.disabled = True
	
	async def callback(self, ctx: miru.ViewContext):
		self.modal= GenModal(title= self.title)
		for input in deepcopy(self.inputs):
			self.modal.add_item(input)
		self.refresh()
		await ctx.respond_with_modal(self.modal)
		await self.modal.wait()

# generic modal
class GenModal(miru.Modal):
	async def callback(self, ctx: miru.ModalContext):
		values= ""
		for value in list(self.children):
			if values:
				values+= ", "
			values+= value.label
		await ctx.edit_response(f"Values saved. ({values})")

# generic add button
class AddButton(ModalButton):
	def __init__(
		self,
		title: str,
		inputs= [miru.TextInput(label="Name", placeholder="Input name.", required=True, max_length=30),],
		template: dict= None
		):
		self.temp= template
		super().__init__(
		inputs= inputs,
		title= title,
		emoji= chr(0x2795), 
		style= ButtonStyle.SUCCESS,
		row= 1
		)
	
	def onChange(self):
		pass
		
	async def callback(self, ctx: miru.ViewContext):
		length= len(self.view.panels[self.view.now].comp)
		await super().callback(ctx)
		name= list(self.modal.values)[0].value
		self.view.obj["names"].append(name)
		i= len(self.view.obj["names"])-1
		if len(self.inputs) == 2:
			self.view.obj[i]= list(self.modal.values)[1].value
		else:
			self.view.obj[i]= deepcopy(self.temp)
		await views.updateComp(self.view, ctx, range(1, length))
		await views.updateEmbed(self.view)
		
# value edit button
class ValueEdit(ModalButton):
	def __init__(self, inputs, title: str, keys= None, **kwargs):
		if not kwargs:
			kwargs["emoji"]= chr(0x270F)
			kwargs["style"]= ButtonStyle.SECONDARY
			kwargs["row"]= 1
		super().__init__(inputs, title, **kwargs)
		self.keys= keys
			
	# set default values from keys in obj
	def refresh(self):
		if self.keys:
			for i, key in enumerate(self.keys):
				# key "/r" is root
				if key == "/r":
					self.modal.children[i].value= self.view.obj["names"][self.view.page]
				# key "/n" is numbered values
				elif key == "/n":
					self.modal.children[i].value= self.view.obj[self.view.page]
				elif self.view.page is not None:
					self.modal.children[i].value= str(self.view.obj[self.view.page][key])
				else:
					self.modal.children[i].value= str(self.view.obj[key])
					
	async def callback(self, ctx: miru.ViewContext):
		await super().callback(ctx)
		# get list of all user input
		values= list(self.modal.values)
		updated= {}
		# save values in keys
		for i, key in enumerate(self.keys):
			value= values[i].value
			if key == "/r":
				self.view.obj["names"][self.view.page]= value
			elif key == "/n":
				self.view.obj[self.view.page]= value
			else:
				if value:
					out= value
				else:
					out= 0
				updated[key]= out
		if self.view.page is None:
			self.view.obj.update(updated)
		elif updated:
			self.view.obj[self.view.page].update(updated)
		if hasattr(self.view, 'og'):
			view= self.view.og
		else:
			view= self.view
		await views.updateEmbed(view)
		
# edit interface button
class UIEdit(miru.Button):
	def __init__(self, items, **kwargs):
		if not kwargs:
			kwargs["emoji"]= chr(0x270F)
			kwargs["style"]= ButtonStyle.SECONDARY
			kwargs["row"]= 1
		super().__init__(**kwargs)
		self.items= items
		
	# onChange affects button availability
	def onChange(self):
		if len(self.view.obj) > 1:
			self.disabled = False
		else:
			self.disabled = True

	async def callback(self, ctx: miru.ViewContext):
		# set new view
		view= GenView(deepcopy(self.items), self.view, self.view.obj)
		msg= await ctx.respond(components= view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait()

# generic view
class GenView(miru.View):
	def __init__(self, items, og: miru.View, obj: dict= None, timeout: int = 30.0):
		super().__init__(timeout= timeout)
		# set og view and page
		self.og= og
		self.page= og.page
		self.obj= obj
		for item in items:
			self.add_item(item)
			# edit components
			if hasattr(item, 'onChange'):
				item.onChange()
		
	async def on_timeout(self):
		try:
			await self.message.delete()
		except:
			pass

# name(& fp) input button: calls modal
class NameButton(ValueEdit):
	def __init__(self):
		inputs= [
			miru.TextInput(label="Name", placeholder="Input name.", required=True, max_length=30),
		]
		# adjust according to scenario
		if c.enemy:
			label= "Name"
			keys= ["/r", ]
		else:
			label= "Name & FP"
			keys= ["name", "fp"]
			inputs.append(
				miru.TextInput(label="FP", placeholder="Input default flower points.", required=True, max_length=2)
			)
		title= f"Edit {label}"
		super().__init__(
		inputs= inputs,
		keys= keys,
		title= title,
		label= label,
		style= ButtonStyle.SECONDARY,
		row=2
		)
		
# Stat Input Button: calls modal
class StatButton(ValueEdit):
	def __init__(self):
		inputs= [
			miru.TextInput(label="HP", placeholder="Input maximum health points.", required=True, max_length=3),
			miru.TextInput(label="POW", placeholder="Input default attack power.", required=True, max_length=2),
			miru.TextInput(label="DEF", placeholder="Input default defense points. (If empty, DEF = 0)", max_length=2),
			miru.TextInput(label="Speed", placeholder="Input default speed points. (If empty, Speed = 0)", max_length=2),
			miru.TextInput(label="Stache", placeholder="Input default stache points. (If empty, Stache = 0)", max_length=2)
		]
		if c.enemy:
			name= "enemies"
		else:
			name= "player"
		super().__init__(
		inputs= inputs,
		keys= ["HP", "POW", "DEF", "SPEED", "STACHE"],
		label="Other Stats",
		title= "Edit Stats",
		style= ButtonStyle.SECONDARY,
		row=2
		)

# move editor panel
class MovePanel(views.Panel):
	def __init__(self, index: int= None):
		if not c.moves:
			if c.enemy:
				self.index= index
				c.moves= c.save["enemies"][self.index]["moves"]
			else:
				c.moves= c.save["moves"]
		items= [
			AddButton(template= {"info": "", "icon": "", "amount": 0, "hits": 1, "cost": 0, "offense": True, "rarity": "Normal", "type": "Ground", "target": "One", "stat": "HP"},
			title= "New Move"
			),
			UIEdit(
			items= [
			MoveEdit(),
			MoveOff(),
			MoveTar(),
			MoveType(),
			MoveStat()
			]),
			DupButton(),
			DelButton()
		]
		if not c.enemy:
			items[1].items.append(MoveRare())
		super().__init__(components= items, obj= c.moves)
		
	def onEdit(self):
		if c.save.get("mode") == "badge":
			costCh = True
		else: 
			costCh = False
		if c.enemy:
			c.save["enemies"][self.index]["moves"]= c.moves
		else:
			c.save["moves"]= c.moves
		if len(c.moves) > 1:
			self.embeds= []
			for i in range(len(c.moves)-1):
				name= c.moves["names"][i]
				value= c.moves[i]
				info= ""
				if not c.enemy:
					info= f"Info: {value['info']}\nRarity: {value['rarity']}, Emote: {value['icon']}\n"
				info+= f"This {value['type']} move "
				if value["offense"]:
					if value["stat"] == "HP":
						info+= f"does {value['amount']} damage to "
					else:
						info+= f"decreases {value['amount']} {value['stat']} to "
				else:
					if value["stat"] == "HP":
						info+= f"heals "
					else:
						info+= f"increases "
					info+= f"{value['amount']} {value['stat']} for "
				if value["target"] == "One":
					info+= f"one target "
				elif value["target"] == "All":
					info+= f"all targets "
				else:
					info+= f"a random target "
				info+= f"and hits {value['hits']} time(s)."
				if costCh:
					info+= f"\nFP Cost (Badges Mode): {value['cost']}"
				embed= c.StEmbed(title=name, description=info)
				self.embeds.append(embed)
		else:
			self.embeds= c.StEmbed(title="No moves available.", description="Add a move and it will appear.")
			
# move edit screen: calls modal
class MoveEdit(ValueEdit):
	def __init__(self):
		# set inputs
		inputs=[
			miru.TextInput(label="Name", placeholder="Input move name.", max_length=20, required=True),
			miru.TextInput(label="Amount", placeholder="Input amount to add/remove.", max_length=2, required=True),
			miru.TextInput(label="Hits", placeholder="Input no. of times the move hits.", max_length=1, required=True)
			]
		keys= ["/r", "amount", "hits"]
		# add extra values
		extra= []
		eKeys= []
		if not c.enemy:
			extra.append(miru.TextInput(label="Info", placeholder="Input move description.", max_length=45, required=True))
			eKeys.append("info")
			if c.save.get("mode") == "badge":
				extra.append(miru.TextInput(label="Cost", placeholder="Input FP cost.", max_length=2))
				eKeys.append("cost")
			else:
				extra.append(miru.TextInput(label="Emote", placeholder="Input reaction emote.", max_length=40, required=True))
				eKeys.append("icon")
		for i, item in enumerate(extra):
			inputs.insert(1, item)
			keys.insert(1, eKeys[i])
		super().__init__(
		inputs= inputs,
		keys= keys, 
		title= "Edit Move",
		label= "Edit",
		style= ButtonStyle.SECONDARY
		)
		
# move rarity toggle
class MoveRare(SwitchButton):
	def __init__(self):
		super().__init__(
		options = ["Normal", "Shiny", "Flashy"],
		emojis = [chr(0x1F7E1), chr(0x2728), chr(0x1F4A5)]
		)

	def onChange(self):
		if self.index is None:
			self.label = c.moves[self.view.page]["rarity"]
		super().onChange()
		
	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		c.moves[self.view.page]["rarity"] = self.options[self.index]
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 5)

# move offense toggle
class MoveOff(SwitchButton):
	def __init__(self):
		super().__init__(
		options = ["Attack", "Recover/Buff"],
		emojis = [chr(0x1F525), chr(0x1F496)]
		)
		
	def onChange(self):
		if self.index is None:
			if not c.moves[self.view.page]["offense"]:
				self.index= 1
			else:
				self.index= 0
		super().onChange()
			
	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		if bool(self.index):
			c.moves[self.view.page]["offense"] = False
		else:
			c.moves[self.view.page]["offense"] = True
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 1)

# move target selection
class MoveTar(SwitchButton):
	def __init__(self):
		super().__init__(
		options = ["One", "All", "Random"],
		emojis = [chr(0x1F464), chr(0x1F465), chr(0x2754)]
		)

	def onChange(self):
		if self.index is None:
			self.label= c.moves[self.view.page]["target"]
		super().onChange()
		
	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		c.moves[self.view.page]["target"] = self.options[self.index]
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 2)

# move type toggle
class MoveType(SwitchButton):
	def __init__(self):
		super().__init__(
		options = ["Ground", "Aerial", "Magic"],
		emojis = [chr(0x1F45E), chr(0x1F985), chr(0x1FA84)]
		)

	def onChange(self):
		if self.index is None:
			self.label = c.moves[self.view.page]["type"]
		super().onChange()
		
	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		c.moves[self.view.page]["type"] = self.options[self.index]
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 3)

# move affected stat toggle
class MoveStat(SwitchButton):
	def __init__(self):
		super().__init__(
		options = ["HP", "FP", "POW", "DEF", "SPEED", "STACHE"],
		emojis = [chr(0x2665), chr(0x1F33B), chr(0x1F4A5), chr(0x1F6E1), chr(0x1F45F), chr(0x1F978)]
		)

	def onChange(self):
		if self.index is None:
			self.label = c.moves[self.view.page]["stat"]
		super().onChange()
		
	async def callback(self, ctx: miru.ViewContext):
		super().callback(ctx)
		c.moves[self.view.page]["stat"] = self.options[self.index]
		await views.updateEmbed(self.view.og)
		await views.updateComp(self.view, ctx, 4)

# generic duplication button
class DupButton(miru.Button):
	def __init__(self):
		super().__init__(
		emoji=chr(0x1F4CB),
		row=1
		)
		
	def onChange(self):
		if len(self.view.obj) > 1:
			self.disabled = False
		else: 
			self.disabled = True
			
	async def callback(self, ctx: miru.ViewContext):
		# save to new item
		self.view.obj["names"].append(self.view.obj["names"][self.view.page])
		self.view.obj[len(self.view.obj)-1] = deepcopy(self.view.obj[self.view.page])
		await views.updateEmbed(self.view)

# generic delete button
class DelButton(miru.Button):
	def __init__(self):
		super().__init__(
		emoji=chr(0x1F5D1),
		style=ButtonStyle.DANGER,
		row=1
		)
		
	def onChange(self):
		if len(self.view.obj) > 1:
			self.disabled = False
		else: self.disabled = True
		
	async def callback(self, ctx: miru.ViewContext) -> None:
		length= len(self.view.panels[self.view.now].comp)
		self.view.obj.pop(self.view.page)
		self.view.obj["names"].pop(self.view.page)
		if self.view.page == len(self.view.pages)-1:
			self.view.page-=1
		else:
			for i in range(self.view.page, len(self.view.obj)-1):
				self.view.obj[i]= self.view.obj.pop(i+1)
		await views.updateComp(self.view, ctx, range(1, length))
		await views.updateEmbed(self.view)