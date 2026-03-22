'''
Components used in the Battle Editor.
'''

import re
import os
import json
import miru
import asyncio
import sql_tools
import config as c
import interface.screens as scr
import interface.gen_comp as comp
from hikari import ButtonStyle, MessageFlag, TextInputStyle

btl_data = 'text/battle.json'


class PhasePanel(scr.SetScreen):
    '''
    phase editor panel
    '''

    def __init__(self, menu):
        super().__init__(
            menu=menu,
            key="phases",
            components=[
                SpawnEnemies(),
                comp.DelButton(),
                Advanced()
            ]
        )

    def onEdit(self):
        if len(self.obj) > 1:
            self.embeds = []
            for i in range(len(self.obj)-1):
                conditions = self.obj["names"][i]
                results = self.obj[i]
                self.embeds.append(
                    c.StEmbed(title=conditions, description=results))
            return

        phase_txt = c.getAsset(btl_data)['editor']['phases']
        if len(self.view.save["enemies"]) > 1:
            self.embeds = c.StEmbed(
                title=phase_txt.get('empty'),
                description=phase_txt.get('no_phase')
            )
        else:
            self.embeds = c.StEmbed(
                title=phase_txt.get('empty'),
                description=phase_txt.get('no_enemy')
            )


class EnemyPanel(scr.SetScreen):
    '''
    enemy editor panel
    '''

    def __init__(self):
        super().__init__(
            key="enemies",
            components=[
                comp.AddButton(
                    template=c.def_enemy,
                    title=c.getAsset(btl_data)['editor']['enemies']['new']
                ),
                comp.UIEdit(
                    items=[
                        comp.NameButton(True),
                        comp.StatButton(),
                        comp.ToggleButton("SPINY", "Spiny"),
                        comp.ToggleButton("FLYING", "Flying")
                    ]),
                comp.DupButton(),
                comp.DelButton(),
                Moves()
            ]
        )

    def onEdit(self):
        if len(self.obj) > 1:
            self.embeds = []
            for i in range(len(self.obj)-1):
                name = self.obj["names"][i]
                enemy = self.obj[i]
                info = c.printEntityData(enemy)
                self.embeds.append(c.StEmbed(title=name, description=info))
        else:
            empty_txt = c.getAsset(
                btl_data)['editor']['enemies']['empty']
            self.embeds = c.StEmbed(
                title=empty_txt['title'],
                description=empty_txt['desc']
            )


class CharPanel(scr.SetScreen):
    '''
    character editor panel
    '''

    def __init__(self):
        char_modal = c.getAsset(btl_data)['editor']['chars']
        char_name = char_modal['name']
        char_url = char_modal['url']
        inputs = [
            miru.TextInput(
                label=char_name['label'], placeholder=char_name['placeholder'],
                required=True, max_length=30),
            miru.TextInput(
                label=char_url['label'], placeholder=char_url['placeholder'],
                required=True, max_length=100)
        ]
        super().__init__(key="dialogue",
                         components=[
                             comp.AddButton(
                                 title=char_modal['add'],
                                 inputs=inputs
                             ),
                             comp.ValueEdit(
                                 keys=["/r", "/n"],
                                 title=char_modal['edit'],
                                 inputs=inputs
                             ),
                             comp.DupButton(),
                             comp.DelButton(),
                             Dialogue()
                         ])

    def onEdit(self):
        chars = self.obj["chars"]
        if len(chars) > 1:
            self.embeds = []
            for i in range(len(chars)-1):
                name = chars["names"][i]
                url = chars[i]
                nEmbed = c.StEmbed(title=name)
                nEmbed.set_thumbnail(url)
                self.embeds.append(nEmbed)
        else:
            char_txt = c.getAsset(
                btl_data)['editor']['chars']
            self.embeds = c.StEmbed(
                title=char_txt['title'],
                description=char_txt['desc']
            )


class EventPanel(scr.SetScreen):
    '''
    dialogue event editor panel
    '''

    def __init__(self):
        super().__init__(key="dialogue",
                         components=[
                             EventMod(),
                             EventMod(edit=True),
                             DupEvent(),
                             DelEvent(),
                             Chars()
                         ])

    def onEdit(self):
        # set events list
        events = self.obj["events"]
        if events:
            # set embeds
            self.embeds = []
            # for each event in list
            for event in events:
                # set embeds for one message
                dEmbeds = []
                # for each name
                for i, content in event:
                    name = self.view.save["dialogue"]["chars"]["names"][int(
                        i)-1]
                    url = self.view.save["dialogue"]["chars"][int(i)-1]
                    if url:
                        # create new embed
                        nEmbed = c.StEmbed(
                            title=name, description=f'"{content}"')
                        nEmbed.set_thumbnail(url)
                        dEmbeds.append(nEmbed)
                # append to embeds
                self.embeds.append(dEmbeds)
        else:
            event_txt = c.getAsset(
                btl_data)['editor']['events']['label']
            self.embeds = c.StEmbed(
                title=event_txt['title'], description=event_txt['desc'])

# Battle Editor Components


class SpawnEnemies(comp.UIEdit):
    '''
    condition add button: calls modal
    '''

    def __init__(self):
        super().__init__(
            items=[
                EnemySelect(),
                DelSpawn(),
                ClearSpawn()
            ],
            label=c.getAsset(
                btl_data)['editor']['enemies']['spawn'],
            row=1
        )

    def on_change(self):
        if len(self.view.save["enemies"]) > 1:
            self.disabled = False
        else:
            self.disabled = True


class EnemySelect(miru.TextSelect):
    '''
    enemy selection
    '''

    def __init__(self):
        super().__init__(
            options=[miru.SelectOption(label="n/a")],
            placeholder=c.getAsset(
                btl_data)['editor']['enemies']['add'],
            disabled=True
        )

    def on_change(self):
        if self.view.save["enemies"]["names"]:
            self.disabled = False
            options = []
            for i, enemy in enumerate(self.view.save["enemies"]["names"]):
                options.append(
                    miru.SelectOption(label=enemy, value=str(i))
                )
        else:
            self.disabled = True
        self.options = options

    async def callback(self, ctx: miru.ViewContext):
        # set up modal
        num_txt = c.getAsset(btl_data)['editor']['enemies']['num']
        self.is_default = False
        modal = comp.GenModal(title=num_txt['title'])
        modal.add_item(miru.TextInput(
            label=num_txt['label'], placeholder=num_txt['placeholder'],
            required=True, max_length=1))
        await ctx.respond_with_modal(modal)
        await modal.wait()
        # outputting spawn syntax
        spawn = f"spawn:{int(self.values[0])+1},{list(modal.values)[0].value}"
        if hasattr(self.view, "num"):
            out = "&" + spawn
            self.obj[self.view.num] += out
        else:
            if len(self.obj) > 1:
                out = "e0:0hp"
                self.view.num = self.view.page+1
            else:
                out = "start"
                self.view.num = 0
            self.obj["names"].append(out)
            self.obj[self.view.num] = spawn
        # updating root embed and components
        await scr.updateEmbed(self.view.og)
        await scr.updateComp(self.view, ctx)
        await scr.updateComp(self.view.og, ctx)


class DelSpawn(comp.DelButton):
    '''
    delete recent spawn
    '''

    def __init__(self):
        super().__init__()
        self.label = c.getAsset(
            btl_data)['editor']['enemies']['delete']

    def on_change(self):
        if hasattr(self.view, "num"):
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        self.obj[self.view.num] = re.sub(
            r"&(?!.*&).+$", "", self.obj[self.view.num])
        if not self.obj[self.view.num]:
            self.obj.pop(self.view.num)
            self.obj["names"].pop(self.view.num)
            delattr(self.view, "num")
            await scr.updateComp(self.view, ctx)
            await scr.updateComp(self.view.og, ctx)
        if self.view.page == len(self.view.og.pages):
            self.view.og.page -= 1
        await scr.updateEmbed(self.view.og)


class ClearSpawn(miru.Button):
    '''
    clear all spawns
    '''

    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['enemies']['clear'],
            style=ButtonStyle.SECONDARY,
            emoji=chr(0x1F6AB)
        )

    def on_change(self):
        if hasattr(self.view, "num"):
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        self.obj.pop(self.view.num)
        self.obj["names"].pop(self.view.num)
        delattr(self.view, "num")
        await scr.updateComp(self.view, ctx)
        await scr.updateComp(self.view.og, ctx)
        if self.view.page == len(self.view.og.pages):
            self.view.og.page -= 1
        await scr.updateEmbed(self.view.og)

# advanced options button


class Advanced(comp.SwitchButton):
    def __init__(self):
        super().__init__(
            options=[
                miru.SelectOption(emoji='🔽', label=''),
                miru.SelectOption(emoji='🔼', label='')
            ],
            row=1
        )

    def on_change(self):
        if self.index is None:
            self.index = 0
        super().on_change()

    async def callback(self, ctx: miru.ViewContext):
        cond_txt = c.getAsset(btl_data)['editor']['condition']
        inputs = [
            miru.TextInput(
                label=cond_txt['if']['label'],
                placeholder=cond_txt['if']['placeholder'],
                required=True, max_length=50),
            miru.TextInput(
                label=cond_txt['then']['label'],
                placeholder=cond_txt['then']['placeholder'],
                required=True, max_length=100),
        ]
        items = [
            comp.AddButton(inputs=inputs,
                           title=cond_txt['add'],
                           ),
            comp.ValueEdit(inputs=inputs,
                           keys=["/r", "/n"],
                           title=cond_txt['set'],
                           ),
            comp.DupButton()
        ]
        if self.emoji == '🔽':
            for item in items:
                item.row = 2
                self.view.add_item(item)
                self.view.panels[self.view.now].comp.append(item)
                item.on_change()
        else:
            for i in reversed(range(3, 6)):
                item = self.view.panels[self.view.now].comp[i]
                self.view.remove_item(item)
                self.view.panels[self.view.now].comp.pop()
        await super().callback(ctx)

# to moves menu


class Moves(miru.Button):
    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['moves'],
            row=2
        )

    def on_change(self):
        if len(self.obj) > 1:
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        # set move panel
        self.view.panels[self.view.now] = comp.MoveScreen(self.view.page, True)
        # add back button
        self.view.panels[self.view.now].comp.append(Back())
        # swap view
        await self.view.swapView(ctx, int(self.view.now))

# back to enemy view


class Back(miru.Button):
    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['back'],
            row=2
        )

    async def callback(self, ctx: miru.ViewContext):
        # set enemy view items
        self.view.panels[self.view.now] = EnemyPanel()
        # swap view
        await self.view.swapView(ctx, int(self.view.now))

# to dialogue menu


class Dialogue(miru.Button):
    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['dialogue'],
            row=2
        )

    def on_change(self):
        if len(self.obj["chars"]) > 1:
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        # set event panel
        self.view.panels[self.view.now] = EventPanel()
        # swap view
        await self.view.swapView(ctx, int(self.view.now))

# event addition/edit modal


class EventMod(comp.ModalButton):
    def __init__(self, edit: bool = False):
        event_txt = c.getAsset(
            btl_data)['editor']['events']
        self.edit = edit
        if self.edit:
            emoji = chr(0x270F)
            style = ButtonStyle.SECONDARY
            title = event_txt['edit']
        else:
            emoji = chr(0x2795)
            style = ButtonStyle.SUCCESS
            title = event_txt['add']
        label_txt = event_txt['label']

        super().__init__(
            inputs=[
                miru.TextInput(
                    label=label_txt['title'],
                    placeholder=label_txt['desc'],
                    style=TextInputStyle.PARAGRAPH,
                    required=True,
                    max_length=500
                ),
            ],
            title=title,
            emoji=emoji,
            style=style,
            row=1
        )

        def refresh(self):
            if self.edit:
                value = ""
                # array to modifiable input
                for event in self.obj["events"][self.view.page]:
                    value += f"{event[0]}:{event[1]}\n"
            else:
                value = None
            self.modal.children[0].value = value

        def on_change(self):
            if len(self.obj["events"]) > 0:
                self.disabled = False
            elif self.edit:
                self.disabled = True

        async def callback(self, ctx: miru.ModalContext) -> None:
            await super().callback(ctx)
            # get event info
            event = list(self.modal.values)[0].value
            arr = []
            # insert into array
            for dialogue in event.split("\n"):
                arr.append(dialogue.split(":"))
            # if edit
            if self.edit:
                self.obj["events"][self.view.page] = arr
            else:
                self.obj["events"].append(arr)
                await scr.updateComp(self.view, ctx, range(1, 4))
            await scr.updateEmbed(self.view)

# duplicate event button


class DupEvent(comp.DupButton):
    def on_change(self):
        if self.obj["events"]:
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        # save to new event
        self.obj["events"].append(self.obj["events"][self.view.page])
        await scr.updateEmbed(self.view)


class DelEvent(comp.DelButton):
    def on_change(self):
        if self.obj["events"]:
            self.disabled = False
        else:
            self.disabled = True

    async def callback(self, ctx: miru.ViewContext):
        # save to new event
        self.obj["events"].pop(self.view.page)

        if self.view.page == len(self.view.pages)-1:
            self.view.page -= 1

        await scr.updateComp(self.view, ctx, range(1, 4))
        await scr.updateEmbed(self.view)

# to character menu


class Chars(miru.Button):
    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['chars']['menu'],
            row=2
        )

    async def callback(self, ctx: miru.ViewContext):
        # set character panel
        self.view.panels[self.view.now] = CharPanel()
        # swap view
        await self.view.swapView(ctx, int(self.view.now))

# add battle to Starlow button


class StAdd(miru.Button):
    def __init__(self):
        super().__init__(
            emoji=chr(0x2B50),
            label=c.getAsset(btl_data)['editor']['save']['label'],
            row=4
        )

    async def callback(self, ctx: miru.ViewContext):
        save_txt = c.getAsset(btl_data)['editor']['save']
        # ask for confirmation
        view = scr.ConfirmView(ctx)
        msg = await ctx.respond(
            content=save_txt['q'],
            components=view,
            flags=MessageFlag.EPHEMERAL
        )
        await view.start(msg)
        await view.wait_for_input()
        view.stop()
        # if said yes
        if view.output:
            battles = sql_tools.loadID(self.view.guild, False)
            for i, battle in enumerate(battles):
                if not battle:
                    # save self.obj to self.save
                    key = self.view.panels[self.view.now].key
                    if key:
                        self.view.save[key] = self.view.obj
                    else:
                        self.view.save = self.view.obj
                    # save
                    sql_tools.saveID(
                        self.view.guild, self.view.save, False, i)
                    self.view.output = True
                    await ctx.edit_response(
                        content=save_txt['a'],
                        components=None
                    )
                    break
                elif i == 4:
                    self.view.output = False
                    await ctx.edit_response(
                        content=save_txt['cap'],
                        components=None
                    )
            # edit confirmation and delete og
            await self.view.message.delete()
            self.view.stop()

# export battle to .json


class JsonExport(miru.Button):
    def __init__(self):
        super().__init__(
            label=c.getAsset(btl_data)['editor']['json']['label'],
            row=4,
            style=ButtonStyle.SECONDARY
        )

    async def callback(self, ctx: miru.ViewContext):
        json_txt = c.getAsset(btl_data)['editor']['json']
        # ask for confirmation
        view = scr.ConfirmView(ctx)
        msg = await ctx.respond(
            content=json_txt['q'],
            components=view,
            flags=MessageFlag.EPHEMERAL
        )
        await view.start(msg)
        await view.wait_for_input()
        view.stop()
        # if said yes
        if view.output:
            # save self.obj to self.save
            key = self.view.panels[self.view.now].key
            if key:
                self.view.save[key] = self.view.obj
            else:
                self.view.save = self.view.obj
                path = os.path.abspath(__file__).replace(
                    "btl_comp.py", "btl.json")
                with open(path, "x") as file:
                    file.write(json.dumps(self.view.save))
                    try:
                        await asyncio.wait_for(
                            await ctx.respond(attachment=path), timeout=10)
                    except Exception as e:
                        await ctx.edit_response(content=e, components=None)
                        os.remove(path)
            # edit confirmation and delete og
            await ctx.edit_response(content=json_txt['a'], components=None)
            await self.view.message.delete()
            self.view.stop()
