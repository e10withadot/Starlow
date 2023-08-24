from hikari import Embed, TextableChannel, ChannelType
# public dictionaries
save = {}
moves = {}
battle = {}
# Starlow embed
class StEmbed(Embed):
	def __init__(self, *args, **kwargs):
		super().__init__(
		color=0xFFF46F,
		*args,
		**kwargs
		)

# bools
# tracking win/lose conditions
win= False
lose= False
# enemy check
enemy= False
# other
channel= TextableChannel(app= None, id= 0, name= None, type= ChannelType.GUILD_TEXT)
members= None