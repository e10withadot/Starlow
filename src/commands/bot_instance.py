'''
Handles bot commands.
'''
import hikari
from hikari import SlashCommand, CommandOption, CommandChoice, CommandType
import miru
import sql_tools
import config as c
from commands.settings import settings
import random
from time import time


class Command:
    '''
    Simple Starlow command wrapper.
    '''

    def __init__(
            self,
            name: str,
            description: str,
            options: list[CommandOption] = hikari.UNDEFINED,
            admin_command: bool = False
    ):
        self.name = name
        self.description = description
        self.options = options
        self.admin = admin_command


class StarlowBot(hikari.GatewayBot):
    '''
    A Starlow Bot instance. Includes the miru client.
    '''

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.client = miru.Client(self, ignore_unknown_interactions=True)
        self.event_manager.subscribe(
            hikari.InteractionCreateEvent, self.run_commands)

    def build_commands(self) -> list[SlashCommand]:
        '''
        Builds all of Starlow's commands.
        '''
        cmd_txt = c.getAsset("text/commands.json")
        # command info
        commands = [
            Command("ping", cmd_txt.get('ping')),
            Command(
                "luigi", cmd_txt.get('luigi')),
            Command(
                "settings", cmd_txt.get('settings'), admin_command=True),
            Command("battle", cmd_txt['battle']['desc'], [
                CommandOption(
                    name="create",
                    description=cmd_txt['battle']['create'],
                    type=hikari.OptionType.SUB_COMMAND
                ),
                CommandOption(
                    name="edit",
                    description=cmd_txt['battle']['edit']['desc'],
                    type=hikari.OptionType.SUB_COMMAND,
                    options=[
                        CommandOption(
                            name="battle",
                            description=cmd_txt['battle']['edit']['battle'],
                            choices=[CommandChoice(name=f"Slot {i}", value=f"{
                                                   i}") for i in range(1, 6)],
                            type=hikari.OptionType.STRING,
                            is_required=True
                        )
                    ]),
                CommandOption(
                    name="start",
                    description=cmd_txt['battle']['start']['desc'],
                    type=hikari.OptionType.SUB_COMMAND,
                    options=[
                        CommandOption(
                            name="battle",
                            description=cmd_txt['battle']['start']['battle'],
                            choices=[CommandChoice(name=f"Slot {i}", value=f"{
                                                   i}") for i in range(1, 6)],
                            type=hikari.OptionType.STRING
                        ),
                        CommandOption(
                            name="file",
                            description=cmd_txt['battle']['start']['file'],
                            type=hikari.OptionType.ATTACHMENT
                        )
                    ])
            ], admin_command=True)
        ]
        # create builders
        builders: list[hikari.impl.SlashCommandBuilder] = []
        for command in commands:
            builder = self.rest.slash_command_builder(
                command.name,
                command.description
            )
            if command.admin:
                builder.set_default_member_permissions(
                    hikari.Permissions.MANAGE_CHANNELS)
            if command.options != hikari.UNDEFINED:
                for option in command.options:
                    builder.add_option(option)
            builders.append(builder)
        return builders

    async def run_commands(self, event: hikari.Event):
        '''
        Handles initialization of slash commands.
        '''
        if isinstance(event.interaction, hikari.CommandInteraction) \
                and event.interaction.command_type == CommandType.SLASH:
            name = event.interaction.command_name
            if name == "ping":
                t = time()
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    "Pong!"
                )
                ct = time() - t
                await event.interaction.edit_initial_response(
                    f"Pong!\nResponse time: {round(ct, 2)}s"
                )

            elif name == "luigi":
                if sql_tools.isLuigi(event.interaction.guild_id):
                    responses = c.getAsset("text/luigi.txt").split("\n")
                    await event.interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        random.choice(responses)
                    )
                else:
                    await c.disabledCmd(event.interaction)
            elif name == "settings":
                await settings(self.client, event)
