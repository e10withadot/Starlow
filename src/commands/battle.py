import re
import time
import sql_tools
import config as c
from slipper import jsonStr
import hikari
from hikari import MessageFlag
import miru
from miru import SelectOption
import btl_logic as btl
import interface.screens as scr
import interface.btl_comp as btlc


async def btl_editor(
        client: miru.Client, event: hikari.InteractionCreateEvent):
    '''
    battle editor initalization
    '''
    # system buttons
    sys = [
        btlc.JsonExport(),
        scr.DismissButton()
    ]
    btl_txt = c.getAsset("text/battle.json")
    edit_txt = btl_txt['editor']
    btl_save: dict
    if hasattr(event.interaction.options, "battle"):
        # get battle slot
        i = int(re.findall(r'\d+', event.interaction.options.battle)[0])-1
        btl_save = sql_tools.loadID(event.interaction.guild_id, False)[i]
        if not btl_save:
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                btl_txt["init"]["no_slot"],
                flags=MessageFlag.EPHEMERAL)
            return
        sys.insert(0, scr.SaveButton())
    else:
        i = None
        btl_save = {"phases": {"names": []}, "enemies": {"names": []},
                    "dialogue": {"chars": {"names": []}, "events": []}}
        sys.insert(0, btlc.StAdd())
    # battle editor options
    options = [
        SelectOption(
            label=edit_txt['phases']['title'],
            description=edit_txt['phases']['description'],
            emoji=chr(0x26F3), is_default=True),
        SelectOption(label=edit_txt['enemies']['title'],
                     description=edit_txt['enemies']['description'],
                     emoji=chr(0x1F9CC)),
        SelectOption(label=edit_txt['events']['title'],
                     description=edit_txt['events']['description'],
                     emoji=chr(0x1F4AC))
    ]
    # current command user
    user = event.interaction.user.id
    menu = scr.MainMenu(user, options, sys)
    # battle slot no. (only on edit)
    menu.choice = i
    if isinstance(menu.pages, list):
        embed1 = menu.pages[0]
    else:
        embed1 = menu.pages
    # Starts UI View with the embed
    await event.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        embed=embed1,
        components=menu
    )
    client.start_view(menu)
    await menu.wait()


async def start_battle(event: hikari.InteractionCreateEvent):
    if event.interaction.options:
        # check for input
        if event.interaction.options[0].type == hikari.OptionType.STRING:
            # get slot index
            i = int(re.findall(r'\d+', event.interaction.options.battle)[0])-1
            # get battle from slot
            btl_info = sql_tools.loadID(event.interaction.guild_id, False)[i]
        elif event.interaction.options[0].type == hikari.OptionType.ATTACHMENT:
            # read file
            async with event.interaction.options[0].value.stream() as f:
                data = await f.read()
            btl_info = jsonStr(data.decode("utf-8"))
        # get settings
        settings = sql_tools.loadID(event.interaction.guild_id)
        # get battle channel
        channel = await event.app.rest.fetch_channel(settings["channel"])
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            content=channel.mention,
            flags=MessageFlag.EPHEMERAL)
        # set member acquisition message
        btl_txt = c.getAsset("text/battle.json")['battle']
        embed = (
            c.StEmbed(title=btl_txt['start']['title'],
                      description=btl_txt['start']['desc'])
            .set_footer(btl_txt['start']['footer'])
        )
        msg = await channel.send(embed=embed)
        await event.app.rest.add_reaction(
            message=msg, channel=channel, emoji="🟡")
        # wait a minute for registration
        time.sleep(60)
        # update message info
        msg = await channel.fetch_message(msg)
        members = msg.reactions[0].count-1
        battle = btl.Battle(members, btl_info, settings)
        await battle.turn_order(event)
    else:
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            content=btl_txt['no_line'],
            flags=MessageFlag.EPHEMERAL)
