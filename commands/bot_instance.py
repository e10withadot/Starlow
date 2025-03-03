'''
Handles bot commands.
'''
import hikari
from hikari import SlashCommand, CommandOption, CommandChoice, CommandType
import miru
import time
import sql_tools
import config as c
from slipper import jsonStr
from interface.set_comp import SettingsMenu, MainScreen
from commands.luigi import luigi

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
        self.name= name
        self.description= description
        self.options= options
        self.admin= admin_command

class StarlowBot(hikari.GatewayBot):
    '''
    A Starlow Bot instance. Includes the miru client.
    '''
    def __init__(self, token: str, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.client= miru.Client(self, ignore_unknown_interactions= True)
        self.event_manager.subscribe(hikari.InteractionCreateEvent, self.run_commands)

    def build_commands(self) -> list[SlashCommand]:
        '''
        Builds all of Starlow's commands.
        '''
        # command info
        commands= [
            Command("ping", "Check if the bot is online."),
            Command("luigi", "Starlow's opinion on Luigi. (May include vulgar language)"),
            Command("settings", "Modify default player and battle settings.", admin_command=True),
            Command("battle", "Create, edit, and export battles.", [
                CommandOption(
                    name= "create",
                    description= "Create a new battle.", 
                    type= hikari.OptionType.SUB_COMMAND
                ),
                CommandOption(
                    name= "edit", 
                    description= "Edit an existing battle.",
                    type= hikari.OptionType.SUB_COMMAND,
                    options= [
                    CommandOption(
                        name= "battle",
                        description= "The battle you want to edit.",
                        choices= [CommandChoice(name= f"Slot {i}", value=f"{i}") for i in range(1, 6)],
                        type= hikari.OptionType.STRING,
                        is_required= True
                    )
                ]),
                CommandOption(
                    name= "start",
                    description= "Start a battle.", 
                    type= hikari.OptionType.SUB_COMMAND,
                    options= [
                    CommandOption(
                        name= "battle",
                        description= "A battle saved in Starlow.", 
                        choices= [CommandChoice(name= f"Slot {i}", value=f"{i}") for i in range(1, 6)],
                        type= hikari.OptionType.STRING
                    ),
                    CommandOption(
                        name= "file",
                        description= "A Starlow-supported .json file.", 
                        type= hikari.OptionType.ATTACHMENT
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
                builder.set_default_member_permissions(hikari.Permissions.MANAGE_CHANNELS)
            if command.options != hikari.UNDEFINED:
                for option in command.options:
                    builder.add_option(option)
            builders.append(builder)
        return builders

    async def run_commands(self, event: hikari.InteractionCreateEvent):
        '''
        Handles initialization of slash commands.
        '''
        # if slash command
        if isinstance(event.interaction, hikari.CommandInteraction) and event.interaction.command_type == CommandType.SLASH:
            name= event.interaction.command_name
            if name == "ping":
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    f"I will dethrone Referee Toad and rule Butt Fables with an iron fist.\nElapsed Time: {time.process_time()}ms."
                )
            elif name == "luigi":
                await luigi(event)
            elif name == "settings":
                await self.settings(event)
    
    async def settings(self, event: hikari.InteractionCreateEvent) -> None:
        '''
        Run the settings command.
        '''
        # check db file for guild key
        loadedSave= sql_tools.loadID(event.interaction.guild_id)
        save= jsonStr(loadedSave) if loadedSave else c.def_settings
        # set user
        user= event.interaction.user
        # build menu
        menu= SettingsMenu(user, save)
        builder = await menu.build_response_async(self.client, MainScreen(menu))
        await builder.create_initial_response(event.interaction)
        # starts view
        self.client.start_view(menu)