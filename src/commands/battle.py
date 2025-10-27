import re
import time
import sql_tools
import config as c
from slipper import jsonStr
import hikari
from hikari import MessageFlag
from miru import SelectOption
import btl_logic as btl
import interface.screens as scr
import interface.btl_comp as btlc


async def btl_editor(event: hikari.InteractionCreateEvent):
    '''
    battle editor initalization
    '''
    # system buttons
    sys = [
        btlc.JsonExport(),
        scr.QuitButton()
    ]
    btl_txt = c.getAsset("text/battle.json")
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
        c.save = btl_save
        sys.insert(0, scr.SaveButton())
    else:
        i = None
        c.save = {"phases": {"names": []}, "enemies": {"names": []},
                  "dialogue": {"chars": {"names": []}, "events": []}}
        sys.insert(0, btlc.StAdd())
    # battle editor options
    options = [
        SelectOption(
            label=btl_txt['phases']['title'],
            description=btl_txt['phases']['description'],
            emoji=chr(0x26F3), is_default=True),
        SelectOption(label=btl_txt['enemies']['title'],
                     description=btl_txt['enemies']['description'],
                     emoji=chr(0x1F9CC)),
        SelectOption(label=btl_txt['events']['title'],
                     description=btl_txt['events']['description'],
                     emoji=chr(0x1F4AC))
    ]
    # Editor panels
    panels = [
        btlc.PhasePanel(),
        btlc.EnemyPanel(),
        btlc.CharPanel()
    ]
    # current command user
    user = event.interaction.user.id
    view = scr.MainView(user, panels, options, sys)
    # battle slot no. (only on edit)
    view.choice = i
    if isinstance(view.pages, list):
        embed1 = view.pages[0]
    else:
        embed1 = view.pages
    # Starts UI View with the embed
    await event.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        embed=embed1,
        components=view
    )
    c.miru_client.start_view(view)
    await view.wait()


async def start_battle(event: hikari.InteractionCreateEvent):
    if event.interaction.options.battle or event.interaction.options.file:
        # check for input
        if event.interaction.options.battle:
            # get slot index
            i = int(re.findall(r'\d+', event.interaction.options.battle)[0])-1
            # get battle from slot
            btl_info = sql_tools.loadID(event.interaction.guild_id, False)[i]
        elif event.interaction.options.file:
            # read file
            async with event.interaction.options.file.stream() as f:
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
