'''
Generic components (Buttons, Selectors, Modals) used across the program.
'''

import miru
from miru.ext import menu
from copy import deepcopy
from hikari import ButtonStyle, MessageFlag, Emoji

class StarlowButton(menu.ScreenButton):
	'''
	Generic Starlow button.
	'''
	def on_change(self):
		'''
		Runs when screen changes.
		'''
		pass

class SwitchButton(StarlowButton):
	'''
	A button that switches between a list of options.
	'''
	def __init__(self, key: str = None, options: list[miru.SelectOption] = None, emojis: list[Emoji]= None, **kwargs):
		super().__init__(style= ButtonStyle.SECONDARY, **kwargs)
		self.key= key
		self.options = options
		if self.options:
			self.label = self.options[0].label
		self.emojis = emojis
		if self.emojis:
			self.emoji = self.emojis[0]
		self.index = None
		
	def on_change(self):
		if self.options:
			# on init
			if self.index is None:
				value= self.screen.obj[self.screen.page][self.key] if self.screen.has_pages() else self.screen.obj[self.key]
				for i, option in enumerate(self.options):
					if option.value == value:
						self.label= option.label
						self.index= i
						break
			# on change
			else:
				self.label = self.options[self.index].label
			self.emoji = self.options[self.index].emoji
		else:
			self.emoji = self.emojis[self.index]
		
	async def callback(self, ctx: miru.ViewContext):
		# change index
		if self.options:
			max_index = len(self.options)-1
		else:
			max_index = len(self.emojis)-1
		if self.index + 1 <= max_index:
			self.index += 1
		else:
			self.index = 0
		# update data
		if self.key:
			if self.options:
				output= self.options[self.index].value
			else:
				output= bool(self.index)
			if self.screen.has_pages():
				self.screen.obj[self.screen.page][self.key] = output
			else:
				self.screen.obj[self.key] = output
		# update menu
		self.on_change()
		await ctx.edit_response(components= self.menu)

class ToggleButton(SwitchButton):
	'''
	Button which toggles between On/Off.
	'''
	def __init__(self, key: str, label: str, emojis: list[Emoji] = None):
		if not emojis:
			emojis= ['🔴', '🟢']
		super().__init__(key, emojis=emojis, label= label)
	
	def on_change(self):
		if self.index is None:
			if self.screen.has_pages():
				self.index= int(self.screen.obj[self.screen.page][self.key])
			else:
				self.index= int(self.screen.obj[self.key])
		super().on_change()

class GhostButton(StarlowButton):
	'''
	Disappears after one input.
	'''
	def on_change(self):
		if len(self.screen.obj) > 1:
			self.disabled = False
		else:
			self.disabled = True

class ModalButton(GhostButton):
	'''
	Button that calls a modal.
	'''
	def __init__(self, inputs, title: str, **kwargs):
		self.inputs= inputs
		self.title= title
		super().__init__(**kwargs)
	
	def refresh(self):
		pass
	
	async def callback(self, ctx: miru.ViewContext):
		self.modal= GenModal(title= self.title)
		for input in deepcopy(self.inputs):
			self.modal.add_item(input)
		self.refresh()
		await ctx.respond_with_modal(self.modal)
		await self.modal.wait()

class GenModal(miru.Modal):
	'''
	Generic modal interface.
	'''
	async def callback(self, ctx: miru.ModalContext):
		values= ""
		for value in list(self.children):
			if values:
				values+= ", "
			values+= value.label

class AddButton(ModalButton):
	'''
	Generic "Add item" button.
	'''
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
		
	async def callback(self, ctx: miru.ViewContext):
		await super().callback(ctx)
		# add name to list
		name= list(self.modal.values)[0].value
		self.screen.obj["names"].append(name)
		i= len(self.screen.obj["names"])-1
		# output to obj
		if len(self.inputs) == 2:
			self.screen.obj[i]= list(self.modal.values)[1].value
		else:
			self.screen.obj[i]= deepcopy(self.temp)
		
# value edit button
class ValueEdit(ModalButton):
	'''
	Button which brings up a modal interface for value editing.
	'''
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
					self.modal.children[i].value= self.screen.obj["names"][self.screen.page]
				# key "/n" is numbered values
				elif key == "/n":
					self.modal.children[i].value= self.screen.obj[self.screen.page]
				elif self.screen.has_pages():
					self.modal.children[i].value= str(self.screen.obj[self.screen.page][key])
				else:
					self.modal.children[i].value= str(self.screen.obj[key])
					
	async def callback(self, ctx: miru.ViewContext):
		await super().callback(ctx)
		# get list of all user input
		values= list(self.modal.values)
		updated= {}
		# save values in keys
		for i, key in enumerate(self.keys):
			value= values[i].value
			if key == "/r":
				self.screen.obj["names"][self.screen.page]= value
			elif key == "/n":
				self.screen.obj[self.screen.page]= value
			else:
				if value:
					out= value
				else:
					out= 0
				updated[key]= out
		if not self.screen.has_pages():
			self.screen.obj.update(updated)
		elif updated:
			self.screen.obj[self.screen.page].update(updated)
		await self.menu.push(self.screen)

class UIEdit(GhostButton):
	'''
	Button that brings up separate view for editing.
	'''
	def __init__(self, items, **kwargs):
		if not kwargs:
			kwargs["emoji"]= chr(0x270F)
			kwargs["style"]= ButtonStyle.SECONDARY
			kwargs["row"]= 1
		super().__init__(**kwargs)
		self.items= items

	async def callback(self, ctx: miru.ViewContext):
		# set new view
		view= GenView(deepcopy(self.items), self.view, self.screen.obj)
		await ctx.respond(components= view, flags= MessageFlag.EPHEMERAL)
		self.view.client.start_view(view)
		await view.wait()

class GenView(miru.View):
	'''
	Generic view interface.
	'''
	def __init__(self, items, og: miru.View, obj: dict= None, timeout: int = 30.0):
		super().__init__(timeout= timeout)
		# set og view and page
		self.og= og
		self.page= og.page
		self.obj= obj
		for item in items:
			self.add_item(item)
			# edit components
			if hasattr(item, 'on_change'):
				item.on_change()
		
	async def on_timeout(self):
		try:
			await self.message.delete()
		except:
			pass

class NameButton(ValueEdit):
	'''
	Calls modal to edit name (and FP if editing Player character).
	'''
	def __init__(self, enemy: bool = False):
		inputs= [
			miru.TextInput(label="Name", placeholder="Input name.", required=True, max_length=30),
		]
		# adjust according to scenario
		if enemy:
			label= "Name"
			keys= ["/r", ]
		else:
			label= "Name & FP"
			keys= ["name", "FP"]
			inputs.append(
				miru.TextInput(label="FP", placeholder="Input default flower points.", required=True, max_length=2)
			)
		title= f"Edit {label}"
		super().__init__(
		inputs= inputs,
		keys= keys,
		title= title,
		label= label,
		style= ButtonStyle.SECONDARY
		)

class StatButton(ValueEdit):
	'''
	Calls modal to edit character stats. (HP, POW, DEF, SPEED, STACHE)
	'''
	def __init__(self):
		inputs= [
			miru.TextInput(label="HP", placeholder="Input maximum health points.", required=True, max_length=3),
			miru.TextInput(label="POW", placeholder="Input default attack power.", required=True, max_length=2),
			miru.TextInput(label="DEF", placeholder="Input default defense points. (If empty, DEF = 0)", max_length=2),
			miru.TextInput(label="Speed", placeholder="Input default speed points. (If empty, Speed = 0)", max_length=2),
			miru.TextInput(label="Stache", placeholder="Input default stache points. (If empty, Stache = 0)", max_length=2)
		]
		super().__init__(
		inputs= inputs,
		keys= ["HP", "POW", "DEF", "SPEED", "STACHE"],
		label="Other Stats",
		title= "Edit Stats",
		style= ButtonStyle.SECONDARY
		)
			
class MoveEdit(ValueEdit):
	'''
	Calls modal to edit move information.
	'''
	def __init__(self, badge: bool, enemy: bool):
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
		if not enemy:
			extra.append(miru.TextInput(label="Info", placeholder="Input move description.", max_length=45, required=True))
			eKeys.append("info")
			if badge:
				extra.append(miru.TextInput(label="Cost", placeholder="Input FP cost.", max_length=2))
				eKeys.append("cost")
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

class DupButton(GhostButton):
	'''
	Generic "Duplicate item" button.
	'''
	def __init__(self):
		super().__init__(
		emoji=chr(0x1F4CB),
		row=1
		)
			
	async def callback(self, ctx: miru.ViewContext):
		# save to new item
		self.screen.obj["names"].append(self.screen.obj["names"][self.screen.page])
		self.screen.obj[len(self.screen.obj)-1] = deepcopy(self.screen.obj[self.screen.page])

# generic delete button
class DelButton(GhostButton):
	'''
	Generic "Delete item" button.
	'''
	def __init__(self):
		super().__init__(
		emoji=chr(0x1F5D1),
		style=ButtonStyle.DANGER,
		row=1
		)
		
	async def callback(self, ctx: miru.ViewContext) -> None:
		self.screen.obj.pop(self.screen.page)
		self.screen.obj["names"].pop(self.screen.page)
		if self.screen.page == len(self.screen.pages)-1:
			self.screen.page-=1
		else:
			for i in range(self.screen.page, len(self.screen.obj)-1):
				self.screen.obj[i]= self.screen.obj.pop(i+1)