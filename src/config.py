'''
Starlow configs and generic functions.
'''
import hikari
from miru import ViewContext
from pathlib import Path
import json

# default save dict
def_settings = {
    "mode": "sticker",
    "coins": 100,
    "hideHP": False,
    "luigi": True,
    "reward-items": ["HP"],
    "reward-set": "all",
    "channel": "",
    "player": {
        "name": "Mario",
        "HP": 10,
        "FP": 5,
        "POW": 1,
        "DEF": 0,
        "SPEED": 0,
        "STACHE": 0
    }
}

# new enemy dict
def_enemy = {
    "HP": 5,
    "POW": 1,
    "DEF": 0,
    "SPEED": 0,
    "STACHE": 0,
    "SPINY": False,
    "FLYING": False,
    "moves": {"names": []}
}


def getAsset(path: str) -> str | dict:
    '''
    Get a Starlow asset.
    '''
    root_path = Path(__file__).resolve().parent.parent
    new_path: Path = root_path / f"share/{path}"
    with open(new_path) as f:
        fext = new_path.as_posix().split(".")[-1]
        if fext == "txt":
            return f.read()
        elif fext == "json":
            return json.loads(f.read())
    return ''


async def disabledCmd(interaction: hikari.CommandInteraction):
    '''
    Sends a default "Command disabled" response.
    '''
    notice = getAsset("text/misc.json").get('disabled_cmd_alert')  # pyright: ignore[reportAssignmentType, reportAttributeAccessIssue]
    await interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE, embed=hikari.Embed(
            title=notice, color=0xFF0000))


def badgeMode(save: dict) -> bool:
    '''
    Check if badge mode is enabled.
    '''
    if save['mode'] == 'badge':
        return True
    return False


def printEntityData(entity: dict) -> str:
    '''
    Prints player stats in a neat string output.
    '''
    output = entity['name'] if entity.get('name') else ""
    stats = [
        "HP",
        "FP",
        "POW",
        "DEF",
        "Speed",
        "Stache",
        "Spiny",
        "Flying",
    ]
    for stat in stats:
        output += f", {stat}: {entity.get(stat.upper())}" \
            if entity.get(stat.upper()) else ""
    output += "."
    return output


class StEmbed(hikari.Embed):
    '''
    Default Starlow embed.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(
            color=0xFFF46F,
            *args,
            **kwargs
        )
