import miru
import sql_tools
import config as c
from slipper import boolTerm
import interface.views as views
import interface.gen_comp as comp
from hikari import ButtonStyle, MessageFlag

# Settings Panels
# battle mode select panel
class ModePanel(views.Panel):
    def __init__(self):
        super().__init__(
        embeds= c.StEmbed(title="Select Battle Mode", description="The battle mode changes how special attacks behave."),
        components= ModeSelect()
        )

# player stat edit panel
class PlayerPanel(views.Panel):
    def __init__(self):
        super().__init__(obj= c.save["player"],
        components= [
        comp.NameButton(), 
        comp.StatButton()
        ])
        
    def onEdit(self):
        player = c.save.get("player")
        title="Player Stats"
        info= f"Name: {player.get('name')}\nHP: {player.get('HP')}\nFP: {player.get('FP')}\nPOW: {player.get('POW')}\nDEF: {player.get('DEF')}\nSpeed: {player.get('SPEED')}\nStache: {player.get('STACHE')}"
        self.embeds= c.StEmbed(title= title, description= info)

# battle rewards panel
class RewardPanel(views.Panel):
    def __init__(self):
        super().__init__(
        embeds= c.StEmbed(title="Select Battle Reward", description="Choose what you get at the end of a battle, and how you get it!"),
        components= [
            Reward(), 
            comp.SwitchButton("set", ['🖐️', '☝️', '👈'], ["All", "Choice", "Random"])
        ],
        obj= c.save['reward']
        )

# miscellaneous settings panel
class MiscPanel(views.Panel):
    def __init__(self):
        super().__init__([
        comp.ToggleButton("hideHP", "Hide HP"),
        comp.ToggleButton("luigi", "/luigi"),
        BtlChannel()
        ],
        obj= c.save
        )
    
    def onEdit(self):
        t1= boolTerm(c.save.get("hideHP"))
        t2= boolTerm(c.save.get("luigi"))
        if c.save['channel']:
            t3= f"<#{c.save['channel']}>"
        else:
            t3= "Not set"
        description= f"__**Hide HP({t1}):**__ Enemy HP is hidden by default. Can be changed on a per-battle basis.\n__**/luigi Command({t2}):**__ This command may be funny, but also has very vulgar language. If you don’t want that in your server, disabling this would be smart.\n__**Battle Channel({t3}):**__ Default channel where battles are hosted."
        self.embeds= c.StEmbed(title="Miscellaneous Settings", description=description)

# Settings Components
# Battle Mode Selection
class ModeSelect(miru.TextSelect):
    def __init__(self):
        # mode options
        options=[
        miru.SelectOption(label="Stickers Mode (Default)", value="sticker", description="Use a variety of stickers for one-use moves! FP = max stickers."),
        miru.SelectOption(label="Badges Mode", value="badge", description="Special attacks cost FP, and can be included with badges!")
        ]
        # determine default mode
        if c.save.get("mode") == "badge":
            options[1].is_default = True
        else:
            options[0].is_default = True
        self.placeholder="Select Mode"
        super().__init__(
        options= options,
        placeholder= self.placeholder
        )
        
    async def callback(self, ctx: miru.ViewContext) -> None:
        c.save.update({"mode": self.values[0]})
    
# Reward Selection
class Reward(miru.TextSelect):
    def __init__(self):
        options=[
		miru.SelectOption(label="HP-Up Heart", value="HP"),
		miru.SelectOption(label="FP-Up Flower", value="FP"),
        miru.SelectOption(label="Speed-Up Soles", value="SPEED"),
		miru.SelectOption(label="Stache-Up Comb", value="STACHE")
		]
        super().__init__(
        options=options,
        placeholder="Select rewards.",
        max_values=4
        )
        
    def onChange(self):
        values = c.save["reward"]["items"]
        if values:
            # check which values to select
            for i, value in enumerate(values):
                option= self.options[i]
                if value == option.value:
                    option.is_default= True

    async def callback(self, ctx: miru.ViewContext) -> None:
        c.save["reward"]["items"] = self.values

# Hosted Channel Selection
class BtlChannel(miru.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Battle Channel")
        self.channel_type=0
        self.value=c.save["channel"]

    async def callback(self, ctx: miru.ViewContext):
        c.save["channel"] = str(self.values[0].id)
        await views.updateEmbed(self.view)
            
# reset settings button
class ResetButton(miru.Button):
	def __init__(self):
		super().__init__(emoji=chr(0x2716), label="Reset", row=4, style= ButtonStyle.DANGER)
	
	async def callback(self, ctx: miru.ViewContext):
		# ask for confirmation
		view = views.ConfirmView(ctx)
		msg= await ctx.respond(content="Are you sure you want to reset? All your changes will be erased (custom moves won’t be erased).", components=view, flags= MessageFlag.EPHEMERAL)
		await view.start(msg)
		await view.wait_for_input()
		view.stop()
		# if said yes
		if view.output:
			# reinsert default settings
			c.save.update({"mode": "sticker", "coins": 100, "hideHP": False, "luigi": True, "reward": {"items": ["HP"], "set": "All"}, "channel": "", "player": {"name": "Mario", "HP": 10, "FP": 5, "POW": 1, "DEF": 0, "SPEED": 0, "STACHE": 0}})
			# save data
			sql_tools.saveID(self.view.guild, c.save)
			# edit confirmation and delete og
			await ctx.edit_response(content="Your settings have been reset.", components=None)
			await self.view.message.delete()
			self.view.stop()