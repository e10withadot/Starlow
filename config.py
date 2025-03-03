'''
Starlow configs and generic functions.
'''
from hikari import Embed
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

def badgeMode(save: dict) -> bool:
	'''
	Check if badge mode is enabled.
	'''
	if save['mode'] == 'badge':
			return True
	return False

class StEmbed(Embed):
	'''
	Default Starlow embed.
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(
		color=0xFFF46F,
		*args,
		**kwargs
		)