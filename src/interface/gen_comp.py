'''
Generic components (Buttons, Selectors, Modals) used across the program.
'''

import miru
from miru.ext import menu
from copy import deepcopy
from hikari import ButtonStyle, MessageFlag, Emoji, NotFoundError
import config as c

misc_data = "text/misc.json"


class StarlowButton(menu.ScreenButton):
    '''
    Generic Starlow button.
    '''

    def on_change(self):
        '''
        Runs when screen changes.
        '''
        pass


class SwitchButton(StarlowButton):
    '''
    A button that switches between a list of options.
    '''

    def __init__(
        self,
        options: list[miru.SelectOption],
        key: str = None,
        **kwargs
    ):
        super().__init__(style=ButtonStyle.SECONDARY, **kwargs)
        self.key = key
        self.options = options
        self.label = self.options[0].label
        self.index = None

    def on_change(self):
        # on init
        if self.index is None:
            value = self.screen.obj[self.screen.page][self.key] \
                if self.screen.has_pages() else self.screen.obj[self.key]
            for i, option in enumerate(self.options):
                if option.value == value:
                    self.label = option.label
                    self.emoji = option.emoji
                    self.index = i
                    break
        # on change
        else:
            self.label = self.options[self.index].label
            self.emoji = self.options[self.index].emoji

    async def callback(self, ctx: miru.ViewContext):
        if self.index + 1 <= len(self.options)-1:
            self.index += 1
        else:
            self.index = 0
        if self.key:
            output = self.options[self.index].value
            print(output)
            if self.screen.has_pages():
                self.screen.obj[self.screen.page][self.key] = output
            else:
                self.screen.obj[self.key] = output
        await self.screen.update_message()


class ToggleButton(SwitchButton):
    '''
    Button which toggles between On/Off.
    '''

    def __init__(self, key: str, label: str, emojis: tuple[Emoji] = None):
        if not emojis:
            emojis = ('🔴', '🟢')
        super().__init__(key=key, options=[
            miru.SelectOption(label=label, emoji=emojis[0]),
            miru.SelectOption(label=label, emoji=emojis[1])
        ], label=label)
        self.options[0].value = False
        self.options[1].value = True

    def on_change(self):
        if self.index is None:
            if self.screen.has_pages():
                self.index = int(self.screen.obj[self.screen.page][self.key])
            else:
                self.index = int(self.screen.obj[self.key])
        super().on_change()


class BackButton(StarlowButton):
    '''
    Button that goes back.
    '''

    def __init__(self):
        super().__init__(label="< Back", row=4)

    async def callback(self, ctx: miru.ViewContext):
        await self.menu.pop()


class GhostButton(StarlowButton):
    '''
    Disappears before one input.
    '''

    def on_change(self):
        if self.screen.obj and len(self.screen.obj) > 1:
            self.disabled = False
        else:
            self.disabled = True


class ModalButton(GhostButton):
    '''
    Button that calls a modal.
    '''

    def __init__(self, inputs, title: str, **kwargs):
        self.inputs = inputs
        self.title = title
        super().__init__(**kwargs)

    def refresh(self):
        '''
        Refreshes the info of the ModalButton's host.
        '''
        pass

    async def callback(self, ctx: miru.ViewContext):
        self.modal = GenModal(title=self.title)
        for input in deepcopy(self.inputs):
            self.modal.add_item(input)
        self.refresh()
        await ctx.respond_with_modal(self.modal)
        await self.modal.wait()


class GenModal(miru.Modal):
    '''
    Generic modal interface.
    '''
    async def callback(self, ctx: miru.ModalContext):
        values = ""
        for value in list(self.children):
            if values:
                values += ", "
            values += value.label


class AddButton(ModalButton):
    '''
    Generic "Add item" button.
    '''

    def __init__(
            self,
            title: str,
            inputs=[miru.TextInput(
                label=c.getAsset(misc_data)['fields']['name']['label'],
                placeholder=c.getAsset(
                    misc_data)['fields']['name']['placeholder'],
                required=True,
                max_length=30),
            ],
            template: dict = None
    ):
        self.temp = template
        super().__init__(
            inputs=inputs,
            title=title,
            emoji=chr(0x2795),
            style=ButtonStyle.SUCCESS,
            row=1
        )

    def on_change(self):
        pass

    async def callback(self, ctx: miru.ViewContext):
        await super().callback(ctx)
        name = list(self.modal.values)[0].value
        self.screen.obj["names"].append(name)
        i = len(self.screen.obj["names"])-1
        if len(self.inputs) == 2:
            self.screen.obj[i] = list(self.modal.values)[1].value
        else:
            self.screen.obj[i] = deepcopy(self.temp)
        await self.screen.update()


class ValueEdit(ModalButton):
    '''
    Button which brings up a modal interface for value editing.
    '''

    def __init__(self, inputs, title: str, keys=None, **kwargs):
        if not kwargs:
            kwargs["emoji"] = chr(0x270F)
            kwargs["style"] = ButtonStyle.SECONDARY
            kwargs["row"] = 1
        super().__init__(inputs, title, **kwargs)
        self.keys = keys

    def refresh(self):
        if self.keys:
            for i, key in enumerate(self.keys):
                # key "/r" is root
                if key == "/r":
                    self.modal.children[i].value = \
                        self.screen.obj["names"][self.screen.page]
                # key "/n" is numbered values
                elif key == "/n":
                    self.modal.children[i].value = \
                        self.screen.obj[self.screen.page]
                elif self.screen.has_pages():
                    self.modal.children[i].value = str(
                        self.screen.obj[self.screen.page][key])
                else:
                    self.modal.children[i].value = str(self.screen.obj[key])

    async def callback(self, ctx: miru.ViewContext):
        await super().callback(ctx)
        values = list(self.modal.values)
        await self.modal.last_context.defer()
        updated = {}
        for i, key in enumerate(self.keys):
            value = values[i].value
            if key == "/r":
                self.screen.obj["names"][self.screen.page] = value
            elif key == "/n":
                self.screen.obj[self.screen.page] = value
            else:
                if value:
                    out = value
                else:
                    out = 0
                updated[key] = out
        if not self.screen.has_pages():
            self.screen.obj.update(updated)
        elif updated:
            self.screen.obj[self.screen.page].update(updated)
        await self.screen.update()


class UIEdit(GhostButton):
    '''
    Button that brings up separate view for editing.
    '''

    def __init__(self, items, **kwargs):
        if not kwargs:
            kwargs["emoji"] = chr(0x270F)
            kwargs["style"] = ButtonStyle.SECONDARY
            kwargs["row"] = 1
        super().__init__(**kwargs)
        self.items = items

    async def callback(self, ctx: miru.ViewContext):
        view = GenView(deepcopy(self.items), self.view, self.screen.obj)
        await ctx.respond(components=view, flags=MessageFlag.EPHEMERAL)
        self.view.client.start_view(view)
        await view.wait()


class GenView(miru.View):
    '''
    Generic view interface.
    '''

    def __init__(
            self,
            items,
            og: miru.View,
            obj: dict = None,
            timeout: int = 30.0
    ):
        super().__init__(timeout=timeout)
        self.og = og
        self.page = og.page
        self.obj = obj
        for item in items:
            self.add_item(item)
            if hasattr(item, 'on_change'):
                item.on_change()

    async def on_timeout(self):
        try:
            await self.message.delete()
        except NotFoundError:
            print(c.getAsset(misc_data)['view_not_found'])


class NameButton(ValueEdit):
    '''
    Calls modal to edit name (and FP if editing Player character).
    '''

    def __init__(self, enemy: bool = False):
        fields = c.getAsset(misc_data)['fields']
        name_txt = fields['name']
        fp_txt = fields['fp']
        edit_txt = fields['edit']
        inputs = [
            miru.TextInput(
                label=name_txt['label'],
                placeholder=name_txt['placeholder'],
                required=True, max_length=30
            ),
        ]
        if enemy:
            label = name_txt['label']
            keys = ["/r", ]
        else:
            label = f"{name_txt['label']} & {fp_txt['label']}"
            keys = ["name", "FP"]
            inputs.append(
                miru.TextInput(
                    label=fp_txt['label'],
                    placeholder=fp_txt['placeholder'],
                    required=True,
                    max_length=2
                )
            )
        title = f"{edit_txt} {label}"
        super().__init__(
            inputs=inputs,
            keys=keys,
            title=title,
            label=label,
            style=ButtonStyle.SECONDARY
        )


class StatButton(ValueEdit):
    '''
    Calls modal to edit character stats. (HP, POW, DEF, SPEED, STACHE)
    '''

    def __init__(self):
        stat_txt = c.getAsset(misc_data)['fields']
        inputs = [
            miru.TextInput(
                label=stat_txt['hp']['label'],
                placeholder=stat_txt['hp']['placeholder'],
                required=True,
                max_length=3
            ),
            miru.TextInput(
                label=stat_txt['pow']['label'],
                placeholder=stat_txt['pow']['placeholder'],
                required=True,
                max_length=2
            ),
            miru.TextInput(
                label=stat_txt['def']['label'],
                placeholder=stat_txt['def']['placeholder'], max_length=2),
            miru.TextInput(
                label=stat_txt['speed']['label'],
                placeholder=stat_txt['speed']['placeholder'], max_length=2),
            miru.TextInput(
                label=stat_txt['stache']['label'],
                placeholder=stat_txt['stache']['placeholder'], max_length=2)
        ]
        super().__init__(
            inputs=inputs,
            keys=["HP", "POW", "DEF", "SPEED", "STACHE"],
            label=f"{stat_txt['other']} {stat_txt['stats']}",
            title=f"{stat_txt['edit']} {stat_txt['stats']}",
            style=ButtonStyle.SECONDARY
        )


class MoveEdit(ValueEdit):
    '''
    Calls modal to edit move information.
    '''

    def __init__(self, badge: bool, enemy: bool):
        fields = c.getAsset(misc_data)['fields']
        inputs = [
            miru.TextInput(
                label=fields['name']['label'],
                placeholder=fields['name']['placeholder'],
                max_length=20,
                required=True
            ),
            miru.TextInput(
                label=fields['amount']['label'],
                placeholder=fields['amount']['placeholder'],
                max_length=2,
                required=True
            ),
            miru.TextInput(
                label=fields['hits']['label'],
                placeholder=fields['hits']['placeholder'],
                max_length=1,
                required=True
            )
        ]
        keys = ["/r", "amount", "hits"]
        extra = []
        eKeys = []
        if not enemy:
            extra.append(miru.TextInput(
                label=fields['info']['label'],
                placeholder=fields['info']['placeholder'],
                max_length=45,
                required=True
            ))
            eKeys.append("info")
            if badge:
                extra.append(miru.TextInput(
                    label=fields['cost']['label'],
                    placeholder=fields['cost']['placeholder'],
                    max_length=2
                ))
                eKeys.append("cost")
            extra.append(miru.TextInput(
                label=fields['emote']['label'],
                placeholder=fields['emote']['placeholder'],
                max_length=40,
                required=True
            ))
            eKeys.append("icon")
        for i, item in enumerate(extra):
            inputs.insert(1, item)
            keys.insert(1, eKeys[i])
        super().__init__(
            inputs=inputs,
            keys=keys,
            title=f"{fields['edit']} {fields['move']}",
            label=fields['edit'],
            style=ButtonStyle.SECONDARY
        )


class DupButton(GhostButton):
    '''
    Generic "Duplicate item" button.
    '''

    def __init__(self):
        super().__init__(
            emoji=chr(0x1F4CB),
            row=1
        )

    async def callback(self, ctx: miru.ViewContext):
        self.screen.obj["names"].append(
            self.screen.obj["names"][self.screen.page])
        self.screen.obj[len(self.screen.obj) -
                        1] = deepcopy(self.screen.obj[self.screen.page])


class DelButton(GhostButton):
    '''
    Generic "Delete item" button.
    '''

    def __init__(self):
        super().__init__(
            emoji=chr(0x1F5D1),
            style=ButtonStyle.DANGER,
            row=1
        )

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.screen.obj.pop(self.screen.page)
        self.screen.obj["names"].pop(self.screen.page)
        if self.screen.page == len(self.screen.pages)-1:
            self.screen.page -= 1
        else:
            for i in range(self.screen.page, len(self.screen.obj)-1):
                self.screen.obj[i] = self.screen.obj.pop(i+1)
