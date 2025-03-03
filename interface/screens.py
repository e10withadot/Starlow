'''
Generic Screen interface elements. Includes standard, settings, and paged screens.
'''
import hikari
import miru
import sql_tools
import interface.gen_comp as comp
import config as c
from collections.abc import Iterable
from typing import Callable
from hikari import ButtonStyle, MessageFlag
from miru.ext import menu as mm

class ScreenSelect(mm.ScreenTextSelect):
	'''
	Screen selection interface.
	'''
	def __init__(self, default_value: int, options: list[miru.SelectOption], **kwargs):
		# set default
		options[default_value].is_default= True
		# set values
		for i, option in enumerate(options):
			option.value=i
			if (i != default_value):
				option.is_default= False
		super().__init__(options=options, row= 3, **kwargs)

	async def callback(self, ctx: miru.ViewContext):
		i= int(self.values[0])
		await self.menu.push(self.menu.screens[i])

class SetScreen(mm.Screen):
	'''
	Generic screen fmor setting parameters.
	'''
	def __init__(self,
			  menu: mm.Menu,
			  components: list[miru.abc.ViewItem] | miru.abc.ViewItem = None,
			  embeds: hikari.Embed | list[hikari.Embed] = None,
			  key: str = None,
			  ):
		super().__init__(menu)
		# set embeds
		self.embeds= embeds
		# add children
		if isinstance(components, Iterable):
			for component in components:
				self.add_item(component)
		else:
			self.add_item(components)
		self.key= key

	async def build_content(self) -> mm.ScreenContent:
		# update children
		for child in self.children:
			if hasattr(child, 'on_change'):
				child.on_change()
		if isinstance(self.embeds, Iterable) > 1:
			return mm.ScreenContent(embeds=self.embeds)
		return mm.ScreenContent(embed=self.embeds)

	# edit object
	@property
	def obj(self):
		if self.key:
			return self.menu.save[self.key]
		return self.menu.save

	@obj.setter
	def obj(self, value):
		if self.key:
			self.menu.save[self.key] = value
		else:
			self.menu.save = value

	def has_pages(self) -> bool:
		'''
		Returns if the screen has pages.
		'''
		return False

# move editor panel
class MoveScreen(SetScreen):
	def __init__(self, menu: mm.Menu, enemy: bool, badge: bool= False, index: int= None):
		self.index= index
		self.enemy= enemy
		self.badge= badge
		items= [
			comp.AddButton(template= {"info": "", "icon": "", "amount": 0, "hits": 1, "cost": 0, "offense": True, "rarity": "Normal", "type": "Ground", "target": "One", "stat": "HP"},
			title= "New Move"
			),
			comp.UIEdit(
			items= [
			comp.MoveEdit(self.badge, self.enemy),
			comp.ToggleButton("offense", 'Offensive'),
			comp.SwitchButton("target", [
				miru.SelectOption("One", "one", emoji= '🚹'), 
				miru.SelectOption("All", "all", emoji= '🚻'),
				miru.SelectOption("Random", "random", emoji= '❔')
			]),
			comp.SwitchButton("type", [
				miru.SelectOption("Ground", "ground", emoji= '🔨'), 
				miru.SelectOption("Aerial", "air", emoji='👞'),
				miru.SelectOption("Magic", "magic", emoji='🎩')
			]),
			comp.SwitchButton("stat", [
				miru.SelectOption("HP", "HP", emoji='♥'),
				miru.SelectOption("FP", "FP", emoji='🌻'),
				miru.SelectOption("POW", "POW", emoji='💥'),
				miru.SelectOption("DEF", "DEF", emoji='🛡'),
				miru.SelectOption("Speed", "SPEED", emoji='👟'),
				miru.SelectOption("Stache", "STACHE", emoji=chr(0x1F978))
			])
			]),
			comp.DupButton(),
			comp.DelButton()
		]
		if not index:
			items[1].items.append(comp.SwitchButton("rarity", [
				miru.SelectOption("Normal", "norm", emoji='🟡'),
				miru.SelectOption("Shiny", "shiny", emoji='✨'),
				miru.SelectOption("Flashy", "flash", emoji='🎆')
			]))
		super().__init__(menu, components= items, key="moves")
	
	@property
	def moves(self):
		if self.enemy:
			return self.menu.save["enemies"][self.index]['moves']
		return self.menu.save['moves']
	
	@moves.setter
	def moves(self, value):
		if self.enemy:
			self.menu.save['enemies'][self.index]['moves'] = value
		else:
			self.menu.save['moves'] = value

	async def build_content(self):
		if len(self.moves) > 1:
			self.embeds= []
			for i in range(len(self.moves)-1):
				name= self.moves["names"][i]
				value= self.moves[i]
				info= ""
				if not self.enemy:
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
				if self.badge:
					info+= f"\nFP Cost (Badges Mode): {value['cost']}"
				embed= c.StEmbed(title=name, description=info)
				self.embeds.append(embed)
		else:
			self.embeds= c.StEmbed(title="No moves available.", description="Add a move and it will appear.")
		return await super().build_content()

class NavButton(comp.StarlowButton):
	'''
	Generic nav button class.
	'''
	def __init__(self, label: str, style: ButtonStyle = ButtonStyle.PRIMARY, last: bool = False):
		self.last= last
		super().__init__(label= label, style= style, row= 0)

	def on_change(self):
		if self.last:
			if self.screen.page == len(self.screen.pages)-1:
				self.disabled = True
			else:
				self.disabled = False
		else:
			if self.screen.page == 0:
				self.disabled = True
			else:
				self.disabled = False

	async def callback(self, ctx: miru.ViewContext):
		await self.menu.push(self.screen)

class FirstButton(NavButton):
	'''
	Goes to first page.
	'''
	def __init__(self):
		super().__init__(label="|<", last=False)

	async def callback(self, ctx: miru.ViewContext):
		self.screen.page=0
		await super().callback(ctx)

class PrevButton(NavButton):
	'''
	Goes back one page.
	'''
	def __init__(self):
		super().__init__(label="<", last=False)

	async def callback(self, ctx: miru.ViewContext):
		self.screen.page-=1
		await super().callback(ctx)

class Indicator(NavButton):
	'''
	Shows page count. Can be clicked to enter page number.
	'''
	def __init__(self):
		super().__init__(label="0/0", style= ButtonStyle.SECONDARY)

	async def callback(self, ctx: miru.ViewContext):
		modal=PageModal(self.screen)
		await ctx.respond_with_modal(modal)
		await super().callback(ctx)
	
	def on_change(self):
		self.label = f"{self.screen.page+1}/{len(self.screen.pages)}"
		
class PageModal(miru.Modal):
	'''
	Modal that appears when selecting Indicator.
	'''
	def __init__(self, screen: mm.Screen):
		super().__init__(title="Page Select")
		self.screen=screen
		self.add_item(miru.TextInput(label="Page", placeholder="Skip to which page?", required=True, value=self.screen.page+1, max_length=2))
		
	async def callback(self, ctx: miru.ViewContext):
		self.screen.page=int(ctx.values[0].value)-1
	
class NextButton(NavButton):
	'''
	Goes forward one page.
	'''
	def __init__(self):
		super().__init__(label=">", last=True)
	
	async def callback(self, ctx: miru.ViewContext):
		self.screen.page+=1
		await super().callback(ctx)

class LastButton(NavButton):
	'''
	Goes to last page.
	'''
	def __init__(self):
		super().__init__(label=">|", last=True)
	
	async def callback(self, ctx: miru.ViewContext):
		self.screen.page=len(self.view.pages)-1
		await super().callback(ctx)

class PagedScreen(SetScreen):
	'''
	Screen object with pages.
	'''
	def __init__(self, menu: mm.Menu, pages: list[hikari.Embed | list[hikari.Embed]]):
		super().__init__(menu, embeds= self.pages[0])
		# set pages
		self.pages= pages
		self.page= 0
		# set page nav
		nav= [FirstButton(), PrevButton(), Indicator(), NextButton(), LastButton()]
		for nav_item in nav:
			self.add_item(nav)

	def build_content(self):
		self.embeds= self.pages[self.page]
		return super().build_content()
	
	def has_pages(self):
		return True

class MainMenu(mm.Menu):
	'''
	Main menu interface object.
	'''
	def __init__(self, user: hikari.User, save: dict, sys: list[miru.abc.ViewItem]):
		super().__init__()
		# command user
		self.user= user
		# dictionary to save to
		self.save= save
		# system buttons
		self.sys= sys

	def __sysadd__(self, screen: SetScreen) -> SetScreen:
		for sys in self.sys:
			screen.add_item(sys)
		return screen
	
	async def build_response_async(
			self, 
			client: miru.Client, 
			starting_screen: SetScreen, 
			*, 
			ephemeral: bool = False
			) -> miru.MessageBuilder:
		return await super().build_response_async(client, self.__sysadd__(starting_screen), ephemeral=ephemeral)

	async def push(self, screen: SetScreen) -> None:
		await super().push(self.__sysadd__(screen))

	# check for user confirmation 
	async def view_check(self, ctx: miru.ViewContext) -> bool:
		# if command user is interaction user
		if self.user == ctx.user:
			# save context and guild id
			self.ctx = ctx
			self.guild= str(ctx.guild_id)
			return True
		
	# message to send on timeout
	async def on_timeout(self) -> None:
		# close view
		await self.ctx.respond(content="The request timed out.\nThe interface will no longer respond to inputs.", flags= MessageFlag.EPHEMERAL)
		await self.message.delete()

# confirmation prompt with yes and no buttons
class ConfirmView(miru.View):
	def __init__(self):
		self.output = False
		super().__init__()
	
	async def on_timeout(self):
		try:
			await self.view.message.delete()
		except:
			pass
	
	@miru.button(label="Yes", style= ButtonStyle.SUCCESS, emoji=chr(0x2714))
	async def yes_button(self, ctx: miru.ViewContext, button: miru.Button):
		self.output = True
		
	@miru.button(label="No", style= ButtonStyle.DANGER, emoji=chr(0x2716))
	async def no_button(self, ctx: miru.ViewContext, button: miru.Button):
		await ctx.edit_response(content= "Cancelled.", components= None)

class AlertButton(comp.StarlowButton):
	def __init__(self, question: str, response: str, action: Callable= None, **kwargs):
		self.question= question
		self.response= response
		self.action= action
		self.output = False
		super().__init__(**kwargs)

	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = ConfirmView()
		await ctx.respond(content=self.question, components=view, flags= MessageFlag.EPHEMERAL)
		self.view.client.start_view(view)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			if self.action:
				self.action(self)
			await ctx.edit_response(content=self.response, components= None)
			await self.view.message.delete()
			self.view.stop()

class DismissButton(AlertButton):
	'''
	Button that dismisses the menu (without saving).
	'''
	def __init__(self):
		super().__init__(
			question="Would you like to quit? Your changes won't be saved.",
            response="Changes not saved.",
            emoji=chr(0x1F6AB), label="Dismiss", row=4, style= ButtonStyle.SECONDARY
		)

def save(button: AlertButton):
	'''
	Saving function for menus.
	'''
	# save
	if hasattr(button.view, "choice"):
		sql_tools.saveID(button.view.guild, button.view.save, False, button.view.choice)
	else:
		sql_tools.saveID(button.view.guild, button.view.save)

class SaveButton(AlertButton):
	'''
	Button that saves a guild's settings to Starlow's database.
	'''
	def __init__(self):
		super().__init__(
			question="Would you like to save these settings?",
            response="Saved",
            action=save,
            emoji=chr(0x1F4BE), label="Save", row=4
		)