import lightbulb
import sql_tools
import config as c
from miru import SelectOption
from hikari import Permissions
import interface.views as views
import interface.gen_comp as comp
import interface.set_comp as set


plugin = lightbulb.Plugin("settings")

@plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(Permissions.MANAGE_CHANNELS))
@lightbulb.command("settings", "Modify default player and battle settings.")
@lightbulb.implements(lightbulb.SlashCommand)
async def settings(ctx: lightbulb.Context) -> None:
    c.enemy= False
    # check db file for guild key
    loadedSave= sql_tools.loadID(ctx.guild_id)
    if loadedSave:
        c.save= loadedSave
    else:
        # default settings
        c.save= {"mode": "sticker", "coins": 100, "hideHP": False, "luigi": True, "reward": {"items": ["HP"], "set": "All"}, "channel": "","player": {"name": "Mario", "HP": 10, "FP": 5, "POW": 1, "DEF": 0, "SPEED": 0, "STACHE": 0}, "moves": {"names": []}}
    
    # Settings Options
    options=[
    SelectOption(label="Select Battle Mode", description="How do you want FP to be handled?", emoji= chr(0x1F47E), is_default= True),
    SelectOption(label="Player Settings", description="Set Player stats and behavior.", emoji= chr(0x1F6B9)),
    SelectOption(label="Move Pool", description="Manage the stickers, items, and badges a player can obtain.", emoji= chr(0x1F3B0)),
    SelectOption(label="Reward Settings", description="Set what you get at the end of every battle!", emoji= chr(0x1F3C5)),
    SelectOption(label="Miscellaneous Settings", description="Set battle channel, hide enemy HP, and disable /luigi.", emoji= chr(0x2699))
    ]
    
    # system buttons (shown in bottom row)
    sys= [
    views.SaveButton(),
    views.QuitButton(),
    set.ResetButton()
    ]
    
    # panel and user setup
    panel1= set.ModePanel()
    embed1= panel1.embeds
    panels= [
        panel1,
        set.PlayerPanel(),
        comp.MovePanel(),
        set.RewardPanel(),
        set.MiscPanel()
        ]
    user= ctx.author
    view= views.MainView(user, panels, options, sys)
    message= await ctx.respond(embed=embed1, components=view)
    # Starts UI View with the embed
    await view.start(message)
    await view.wait()
    
def load(bot):
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)