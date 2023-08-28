import miru
import sql_tools
import config as c
from hikari import ButtonStyle, MessageFlag

# MainView is the main view, all components connect to it
# MainView has a TextSelect component which switches between a list of "panels"(embeds and buttons)
# if a panel has multiple embeds in the same index, a PageNav interface is included which allows the user to browse through the embeds
# writing this sucked and i’m unsure if the reason is discord’s api or hikari-miru

# MainView(user(type:User), sequence:panels(type:Panel), sequence:options(type:SelectOption), sequence:sys(type:Component))
class MainView(miru.View):
	def __init__(self, user, panels, options, sys):
		super().__init__()
		# current panel
		self.now=0
		# all panels
		self.panels= panels
		# all menu options
		self.options= options
		# command user
		self.user= user
		# page navigation
		self.nav=[]
		# current page
		self.page= None
		# add num values to view options
		for i, option in enumerate(self.options):
			option.value=i
		# update obj
		self.obj= self.panels[0].obj
		# update and add embeds
		self.panels[0].onEdit()
		self.pages= self.panels[0].embeds
		# add page navigator if applicable
		if isinstance(self.pages, list):
			pageNav(self)
		# add first view components
		if isinstance(self.panels[0].comp, list):
			for item in self.panels[0].comp:
				self.add_item(item)
				if hasattr(item, 'onChange'):
					item.onChange()
		else:
			self.add_item(self.panels[0].comp)
		# add view selection
		self.add_item(ViewSelect(options=self.options, row=3))
		# add sys buttons at the end
		self.sys= sys
		for button in self.sys:
			self.add_item(button)
		
	# runs before any interaction
	async def view_check(self, ctx: miru.ViewContext) -> bool:
		# if command user is interaction user
		if self.user == ctx.user:
			# save context and guild id
			self.ctx = ctx
			self.guild= str(ctx.guild_id)
			return True
	
	# switches between views
	async def swapView(self, context: miru.ViewContext, swapTo: int):
		# previous option is no longer selected
		self.options[self.now].is_default = False
		# removing all components
		self.clear_items()
		self.nav= []
		# switching current view
		self.now=swapTo
		# update obj
		self.obj= self.panels[self.now].obj
		# update embeds
		self.panels[self.now].onEdit()
		self.pages= self.panels[self.now].embeds
		# if multiple embeds
		if isinstance(self.pages, list):
			# adding page navigation
			pageNav(self)
			fEmbed= self.pages[self.page]
		else:
			self.page= None
			fEmbed= self.pages
		# add all new components
		if isinstance(self.panels[self.now].comp, list):
			for item in self.panels[self.now].comp:
				self.add_item(item)
				# update buttons if applicable
				if hasattr(item, 'onChange'):
					item.onChange()
		else:
			self.add_item(self.panels[self.now].comp)
		# add ViewSelect
		self.add_item(ViewSelect(options=self.options, row=3))
		# add sys buttons
		for button in self.sys:
			self.add_item(button)
		# current option is now selected
		self.options[self.now].is_default = True
		# edit message to display new contents
		if isinstance(fEmbed, list):
			await context.edit_response(embeds=fEmbed, components=self)
		else:
			await context.edit_response(embed=fEmbed, components=self)
	
	# message to send on timeout
	async def on_timeout(self) -> None:
		try:
			# close view
			await self.ctx.respond(content="The request timed out.\nThe interface will no longer respond to inputs.", flags= MessageFlag.EPHEMERAL)
			await self.message.delete()
		except:
			pass

# panel class (includes components and embeds)
class Panel():
	def __init__(self, components, embeds= None, obj: dict= None):
		self.obj= obj
		self.comp= components
		self.embeds= embeds
	
	# runs when embeds are changed
	def onEdit(self):
		pass

# view selection
class ViewSelect(miru.TextSelect):
	async def callback(self, ctx: miru.ViewContext):
		await self.view.swapView(ctx, int(self.values[0]))

# update view component
async def updateComp(view: miru.View, ctx: miru.ViewContext, index: range = None):
	if not index:
		index= range(0, len(view.children))
	# update components
	for i in index:
		item= view.children[i]
		if hasattr(item, 'onChange'):
			item.onChange()
	# edit response to include updated component
	await ctx.edit_response(components=view)

# update current embed
async def updateEmbed(view):
	# edit embeds
	view.panels[view.now].onEdit()
	# initialize
	view.pages= view.panels[view.now].embeds
	# determine the embed to display
	if isinstance(view.pages, list):
		if not view.nav:
			# if doesn’t exist, add pageNav
			pageNav(view)
		else:
			for button in view.nav:
				button.onPageFlip()
		# initiate updated embed
		uEmbed= view.pages[view.page]
	else:
		if view.nav:
			# if pageNav exists, remove it
			for button in view.nav:
				view.remove_item(button)
			view.nav= []
		# initiate updated embed
		uEmbed= view.pages
	# edit response
	if isinstance(uEmbed, list):
		await view.ctx.edit_response(embeds=uEmbed, components=view)
	else:
		await view.message.edit(embed=uEmbed, components=view)

# insert page navigation (proprietary one sucks)
def pageNav(view):
	view.page= 0
	view.nav=[
	FirstButton(label="|<", row=0),
	PrevButton(label="<", row=0), 
	Indicator(label="0/0", style= ButtonStyle.SECONDARY, row=0),
	NextButton(label=">", row=0), 
	LastButton(label=">|", row=0)
	]
	for button in view.nav:
		view.add_item(button)
		button.onPageFlip()

# flip between pages in view
async def flipPage(view, ctx):
	for button in view.nav:
		# onPageFlip disables buttons and updates indicator
		button.onPageFlip()
	for item in view.panels[view.now].comp:
		# reset SwitchButton indexes
		if hasattr(item, 'index'):
			item.index= None
		# onChange modifies buttons according to page
		if hasattr(item, 'onChange'):
			item.onChange()
	if isinstance(view.pages[view.page], list):
		await ctx.edit_response(embeds=view.pages[view.page], components=view)
	else:
		await ctx.edit_response(embed=view.pages[view.page], components=view)

# first button goes to beginning
class FirstButton(miru.Button):
		
	async def callback(self, ctx: miru.ViewContext):
		self.view.page=0
		await flipPage(self.view, ctx)
	
	def onPageFlip(self):
		if self.view.page == 0:
			self.disabled = True
		else:
			self.disabled = False
		
# prev button goes back one page
class PrevButton(miru.Button):
		
	async def callback(self, ctx: miru.ViewContext):
		self.view.page-=1
		await flipPage(self.view, ctx)
		
	def onPageFlip(self):
		if self.view.page == 0:
			self.disabled = True
		else:
			self.disabled = False
	
# indicator to show page count
class Indicator(miru.Button):
	
	async def callback(self, ctx: miru.ViewContext):
		modal=PageModal(self.view)
		await ctx.respond_with_modal(modal)
	
	def onPageFlip(self):
		self.label = f"{self.view.page+1}/{len(self.view.pages)}"
		
# modal that appears when selecting indicator
class PageModal(miru.Modal):
	def __init__(self, view):
		super().__init__(title="Page Select")
		self.view=view
		self.add_item(miru.TextInput(label="Page", placeholder="Skip to which page?", required=True, value=self.view.page+1, max_length=2))
		
	async def callback(self, ctx: miru.ViewContext):
		self.view.page=int(ctx.values[0].value)-1
		await flipPage(self.view, ctx)
	
# next button goes forward one page
class NextButton(miru.Button):
	async def callback(self, ctx: miru.ViewContext):
		self.view.page+=1
		await flipPage(self.view, ctx)
		
	def onPageFlip(self):
		if self.view.page == len(self.view.pages)-1:
			self.disabled = True
		else:
			self.disabled = False
	
# last button goes to end
class LastButton(miru.Button):
	async def callback(self, ctx: miru.ViewContext):
		self.view.page=len(self.view.pages)-1
		await flipPage(self.view, ctx)
		
	def onPageFlip(self):
		if self.view.page == len(self.view.pages)-1:
			self.disabled = True
		else:
			self.disabled = False
		
# confirmation prompt with yes and no buttons
class ConfirmView(miru.View):
	def __init__(self, ctx):
		self.output = False
		super().__init__()
	
	async def on_timeout(self):
		try:
			await self.view.message.delete()
		except:
			pass
	
	@miru.button(label="Yes", style= ButtonStyle.SUCCESS, emoji=chr(0x2714))
	async def yesButton(self, button: miru.Button, ctx: miru.ViewContext):
		c.moves= {}
		self.output = True
		
	@miru.button(label="No", style= ButtonStyle.DANGER, emoji=chr(0x2716))
	async def noButton(self, button: miru.Button, ctx: miru.ViewContext):
		await ctx.edit_response(content= "Cancelled.", components= None)

# save button- view ends after this
class SaveButton(miru.Button):
	def __init__(self):
		super().__init__(emoji=chr(0x1F4BE), label="Save", row=4)
		
	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = ConfirmView(ctx)
		msg= await ctx.respond(content="Would you like to save these settings?", components=view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			# save
			if c.enemy:
				sql_tools.saveID(self.view.guild, c.save, False, self.view.choice)
			else:
				sql_tools.saveID(self.view.guild, c.save)
			# edit confirmation and delete og
			await ctx.edit_response(content="Saved.", components= None)
			await self.view.message.delete()
			self.view.stop()

# dismiss button- view ends without saving		
class QuitButton(miru.Button):
	def __init__(self):
		super().__init__(emoji=chr(0x1F6AB), label="Dismiss", row=4, style= ButtonStyle.SECONDARY)
		
	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = ConfirmView(ctx)
		msg= await ctx.respond(content="Would you like to quit? Your changes won’t be saved.", components=view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			# edit confirmation and delete og
			await ctx.edit_response(content="Changes not saved.", components=None)
			await self.view.message.delete()
			self.view.stop()