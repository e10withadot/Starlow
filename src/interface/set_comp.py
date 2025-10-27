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
        reset_txt = c.getAsset('text/settings.json').get('reset')
        # settings options
        # system buttons (shown in bottom row)
        sys = [
            scr.SaveButton(),
            scr.DismissButton(),
            scr.AlertButton(
                question=reset_txt['q'],
                response=reset_txt['a'],
                action=reset_settings,
                emoji=chr(0x2716),
                label="Reset",
                row=4,
                style=ButtonStyle.DANGER
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
        des = c.getAsset('text/settings.json')['main']['desc']
        super().__init__(
            menu,
            embeds=c.StEmbed(title="Starlow Settings", description=des),
            components=[
                comp.SwitchButton(
                    key="mode",
                    options=[
                        miru.SelectOption(label="Stickers Mode",
                                          value="sticker", emoji='📖'),
                        miru.SelectOption(label="Badges Mode",
                                          value="badge", emoji='🌹')
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
            key="player")

    @menu.button(label="< Back", row=3)
    async def back(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.pop()

    @menu.button(label="Move Pool", emoji="🎰", row=3)
    async def move_pool(self, ctx: miru.ViewContext, button: menu.ScreenButton):
        await self.menu.push(scr.MoveScreen(menu, False, c.badgeMode(self.menu.save)))

    async def build_content(self):
        plyr_info = c.printEntityData(self.obj)
        move_info = ''
        if hasattr(self.menu.save, "moves"):
            for i, move in self.menu.save['moves']:
                if not isinstance(i, str):
                    move_info += f'{move['name']}, '
            move_info.removesuffix(', ')
        else:
            move_info += 'No moves.'
        title = "Player Settings"
        info = f'''### Player Info\n{plyr_info}\n### Moves\n{move_info}'''
        self.embeds = c.StEmbed(title=title, description=info)
        return await super().build_content()

# battle rewards panel


class BattleSettings(scr.SetScreen):
    '''
    Screen for post-battle reward selection.
    '''

    def __init__(self, menu: menu.Menu):

        super().__init__(
            menu,
            components=[
                BtlChannel(),
                comp.ToggleButton("hideHP", "Hide HP"),
                Reward(),
                comp.SwitchButton("reward-set", options=[
                    miru.SelectOption("All", "all", emoji='🖐️'),
                    miru.SelectOption("Choice", "choice", emoji='☝️'),
                    miru.SelectOption("Random", "random", emoji='👈')
                ])
            ])

    async def build_content(self):
        des = c.getAsset('text/settings.json')['main']['battle']['desc']
        self.embeds = c.StEmbed(title="Battle Settings", description=des)
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
        options = [
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
            for i, value in enumerate(values):
                option = self.options[i]
                if value == option.value:
                    option.is_default = True

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.screen.obj["reward-items"] = self.values
        await self.screen.update_message(await self.screen.build_content())


class BtlChannel(menu.ScreenChannelSelect):
    '''
    ChannelSelect object for the channel that battles are hosted in.
    '''

    def __init__(self):
        super().__init__(placeholder="Select Battle Channel")
        self.channel_type = 0

    def on_change(self):
        self.value = self.screen.obj["channel"]

    async def callback(self, ctx: miru.ViewContext):
        self.screen.obj["channel"] = str(self.values[0].id)
        await self.screen.update_message(await self.screen.build_content())


def reset_settings(button: scr.AlertButton):
    '''
    Reset to default settings.
    '''
    button.menu.save.update(c.def_settings)
    sql_tools.saveID(button.menu.guild, button.menu.save)
