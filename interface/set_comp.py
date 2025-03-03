'''
Components used in the Settings command.
'''
import miru
from miru.ext import menu
import sql_tools
import config as c
import interface.screens as scr
import interface.gen_comp as comp
from hikari import ButtonStyle, User

class SettingsMenu(scr.MainMenu):
     '''
     Menu for the Settings command.
     '''
     def __init__(self, user: User, save: dict):
        # settings options
        # system buttons (shown in bottom row)
        sys= [
            scr.SaveButton(),
            scr.DismissButton(),
            scr.AlertButton(
                question="Are you sure you want to reset? All your changes will be erased (custom moves won't be erased).",
                response="Your settings have been reset.",
                action=reset_settings,
                emoji=chr(0x2716), label="Reset", row=4, style= ButtonStyle.DANGER
            )
        ]
        super().__init__(user, save, sys)

# Settings Panels
# battle mode select panel
class MainScreen(scr.SetScreen):
    '''
    Screen for mode selection (Sticker, Badges).
    '''
    def __init__(self, menu: menu.Menu):
        des= '''
### Select Battle Mode
**Stickers Mode (Default):** Use a variety of stickers for one-use moves! FP = max stickers.
**Badges Mode:** Special attacks cost FP, and can be included with badges!

### /luigi command
Starlow insults Luigi in various manners. This command contains vulgar language, therefore, the option to disable it is provided.
        '''
        super().__init__(
        menu,
        embeds= c.StEmbed(title="Starlow Settings", description=des),
        components= [
        comp.SwitchButton(
            key="mode",
            options= [
                miru.SelectOption(label="Stickers Mode", value="sticker", emoji='📖'),
                miru.SelectOption(label="Badges Mode", value="badge", emoji='🌹')
            ]
        ),
        comp.ToggleButton("luigi", "/luigi")
        ]
        )

    @menu.button(label="Player Settings", emoji="👤", row=3)
    async def player_settings(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.push(PlayerSettings(self.menu))

    @menu.button(label="Battle Settings", emoji='⚔', row=3)
    async def battle_settings(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.push(BattleSettings(self.menu))

class PlayerSettings(scr.SetScreen):
    '''
    Screen for Player stat modification.
    '''
    def __init__(self, menu: menu.Menu):
        super().__init__(
        menu,
        [
        comp.NameButton(), 
        comp.StatButton()
        ],
        key= "player")
    
    @menu.button(label="< Back", row=3)
    async def back(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.pop()

    @menu.button(label="Move Pool", emoji="🎰", row=3)
    async def move_pool(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.push(scr.MoveScreen(menu, False, c.badgeMode(self.menu.save)))

    async def build_content(self):
        move_info= ''
        if hasattr(self.menu.save, "moves"):
            for i, move in self.menu.save['moves']:
                if not isinstance(i, str):
                    move_info+= f'{move['name']}, '
            move_info.removesuffix(', ')
        else:
            move_info+= 'No moves.'
        title="Player Settings"
        info= f'''
        ### Player Info
        Name: {self.obj.get('name')}, HP: {self.obj.get('HP')}, FP: {self.obj.get('FP')}, POW: {self.obj.get('POW')}, DEF: {self.obj.get('DEF')}, Speed: {self.obj.get('SPEED')}, Stache: {self.obj.get('STACHE')}.\n
        ### Moves
        {move_info}
        '''
        self.embeds= c.StEmbed(title= title, description= info)
        return await super().build_content()

# battle rewards panel
class BattleSettings(scr.SetScreen):
    '''
    Screen for post-battle reward selection.
    '''
    def __init__(self, menu: menu.Menu):
        
        super().__init__(
        menu,
        components= [
            BtlChannel(),
            comp.ToggleButton("hideHP", "Hide HP"),
            Reward(), 
            comp.SwitchButton("reward-set", options= [
                miru.SelectOption("All", "all", emoji='🖐️'),
                miru.SelectOption("Choice", "choice", emoji='☝️'),
                miru.SelectOption("Random", "random", emoji='👈')
            ])
        ])

    async def build_content(self):
        des=f'''
### Battle Channel
Default channel where battles are hosted. ({self.obj['channel']})

### Hide HP
Enemy HP is hidden by default. Can be changed on a per-battle basis.

### Reward
Choose what you get at the end of a battle, and how you get it.
**Reward Options:** HP-Up Heart, FP-Up Flower, Speed-Up Soles, Stache-Up Comb.
-# Every reward option increases the player's stats by 5.

### Reward Distribution
Choose how the reward is distributed.
- **All:** Distributes every selected reward.
- **Choice:** The server chooses between every selected reward.
- **Random:** The reward is selected randomly.
        '''
        self.embeds= c.StEmbed(title="Battle Settings", description=des)
        return await super().build_content()

    @menu.button(label="< Back", row=3)
    async def back(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.pop()

# Reward Selection
class Reward(menu.ScreenTextSelect):
    '''
    TextSelect object for post-battle reward selection.
    '''
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
        
    def on_change(self):
        values = self.screen.obj["reward-items"]
        if values:
            # check which values to select
            for i, value in enumerate(values):
                option= self.options[i]
                if value == option.value:
                    option.is_default= True

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.screen.obj["reward-items"] = self.values
        await self.menu.update_message(self.screen.build_content())

class BtlChannel(menu.ScreenChannelSelect):
    '''
    ChannelSelect object for the channel that battles are hosted in.
    '''
    def __init__(self):
        super().__init__(placeholder="Select Battle Channel")
        self.channel_type=0

    def on_change(self):
        self.value= self.screen.obj["channel"]

    async def callback(self, ctx: miru.ViewContext):
        self.screen.obj["channel"] = str(self.values[0].id)
        await self.menu.update_message(self.screen.build_content())

def reset_settings(button: scr.AlertButton):
    '''
    Reset to default settings.
    '''
    button.menu.save.update(c.def_settings)
    # save data
    sql_tools.saveID(button.menu.guild, button.menu.save)