'''
Handles settings commands.
'''
import hikari
from miru import Client
import sql_tools
import config as c
from slipper import jsonStr
from interface.set_comp import SettingsMenu, MainScreen


async def settings(client: Client, event: hikari.InteractionCreateEvent) -> None:
    '''
    Run the settings command.
    '''
    loadedSave = sql_tools.loadID(event.interaction.guild_id)
    save = jsonStr(loadedSave) if loadedSave else c.def_settings
    user = event.interaction.user
    menu = SettingsMenu(user, save)
    builder = await menu.build_response_async(client, MainScreen(menu))
    await builder.create_initial_response(event.interaction)
    client.start_view(menu)
