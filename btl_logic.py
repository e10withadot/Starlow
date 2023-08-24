import os
import re
import time
import math
import random
import hikari
import lightbulb
import sql_tools
import config as c
from copy import deepcopy
from slipper import jsonStr, num_to_list

# the Action class defines what battle actions do. Actions can consist of attacks, stickers, moves that cost FP, and items.
class Action:
	def __init__(self, obj: dict, name: str= None, id: int = 0):
		# action id
		self.id= id
		# is shown in battle as an option/the opposing party’s attack.
		self.name= name
		# description. Unnecessary for enemies.
		if obj.get('info'):
			self.info= obj['info']		
		# action type. Options: "Ground", "Aerial", "Magic"
		self.type= obj['type']
		# how much value is reduced/increased.
		self.amount= obj['amount']
		# times an action hits
		self.hits= obj['hits']
		# FP cost of the action. FP isn’t required.
		if obj.get('cost'):
			self.cost= obj['cost']
		# a bool that specifies if the action is offensive.
		self.offense= obj['offense']
		# action target. options: "One, All, Random"
		self.target= obj['target']
		# a string that specifies which stat changes. Options: "HP, FP, POW, DEF, SPEED, STACHE"
		self.stat= obj['stat']
		# likelihood of spawning. Options: "Normal, Shiny, Flashy"
		if obj.get('rarity'):
			self.rarity= obj['rarity']
		# reaction emote
		if obj.get('icon'):
			self.icon= obj['icon']
		# defines whether an Action will be performed only after a condition is met.
		self.scripted= obj.get('scripted')

	# deploy the action
	async def deploy_action(self, target, sender = None, blocked: bool = False):
		for person in target:
			stat= getattr(person, self.stat)
			# check for wrong outcomes
			embed= c.StEmbed(title= "")
			if hasattr(person, "spiny"):
				if self.type == "Aerial" and person.spiny:
					person.HP-=1
					embed.title= f"{sender.name} got hurt by spines!"
					embed.description= "-1HP"
			if hasattr(person, "flying"):
				if self.type == "Ground" and person.flying:
					embed.title= f"{sender.name} can't reach!"
			if person.STACHE == random.random():
				embed.title= f"{sender.name} missed!"
			if embed.title:
				await c.channel.send(embed)
				return
			
			# calculate damage
			if self.offense:
				# if player blocked
				if blocked:
					b= 0.5
				else:
					b= 1
				# if sender exists
				if sender:
					pow= int(sender.POW)
				else:
					pow= 0
				dmg= round((pow + int(self.amount) - int(person.DEF))*b)
				operator= "-"
				# set stat value
				setattr(person, self.stat, int(stat)-dmg*int(self.hits))
			else:
				dmg= int(self.amount)
				operator= "+"
				calc= int(stat)+dmg*int(self.hits)
				# set stat value
				if self.stat == 'HP' or self.stat == 'FP':
					max= getattr(person, f"max{self.stat}")
					if calc > max:
						result= max
					else:
						result= calc
				else:
					result= calc
				setattr(person, self.stat, result)
		# set up response
		embed= c.StEmbed(description= "")
		if self.target == "All":
			name= "all enemies"
		else:
			name= target[0].name
		if sender:
			embed.title= f"{sender.name}: {self.name} -> {name}."
		else:
			embed.title= f"-> {name}."
		# send result
		for hit in range(int(self.hits)):
			embed.description+= f"{operator}{dmg}{self.stat}\n"
			if hit == 0:
				msg= await c.channel.send(embed)
			else:
				msg= await msg.edit(embed)
			time.sleep(0.3)

# the Being class defines the player character, party members, or enemies. It stores their basic stats.
class Being:
	def __init__(self, obj: dict, name: str = None):
		# the Being’s name.
		self.name= name
		# max health points. HP is set to this on init, unless special exception occurs.
		self.maxHP= obj["HP"]
		self.HP= deepcopy(self.maxHP)
		# same as maxHP but FP for special attacks/max sticker cap.
		if obj.get("FP"):
			self.maxFP= obj["FP"]
			self.FP= deepcopy(self.maxFP)
		# set attack power. can flucutate in a battle, and if temporary- value resets to setPOW.
		self.setPOW= obj["POW"]
		self.POW= deepcopy(self.setPOW)
		# same as setPOW, but for defense.
		self.setDEF= obj["DEF"]
		self.DEF= deepcopy(self.setDEF)
		# same as setPOW, but determines turn order. Without speed, player starts.
		self.setSPEED= obj["SPEED"]
		self.SPEED= deepcopy(self.setSPEED)
		# same as setPOW, but determines chance of lucky hits, and may increase store discounts.
		self.setSTACHE= obj["STACHE"]
		self.STACHE= deepcopy(self.setSTACHE)
		# moves is an array of Actions/Action IDs.
		if self.__class__.__name__ == "Player" and c.save["mode"] == "fp" or self.__class__.__name__ == "Enemy" and len(obj["moves"])-1:
			self.moves= []
			for i in range(len(obj["moves"])-1):
				self.moves.append(Action(name= obj["moves"]["names"][i], obj= obj["moves"][i]))
		else:
			self.moves= {}
			
	# adds an Action to self.moves
	def add_move(self, obj: Action):
		self.moves.append(obj)

class Player(Being):
	# adds a sticker
	def add_sticker(self, id: int):
		if not self.FP+1 == 0:
			if id in self.moves.keys():
				self.moves[id]+= 1
			else:
				self.moves[id]= 1
			self.FP-= 1

	# fill sticker inventory with randoms
	async def sticker_roulette(self, ctx: lightbulb.Context, rMoves: list[dict]):
		if c.save["coins"] >= 50:
			emojis= ['1️⃣']
			desc= "Choose an album to use for the battle!\n1️⃣ **Normal Album-** 50 coins."
			if c.save["coins"] >= 100:
				emojis.append('2️⃣')
				desc+= "\n2️⃣ **Shiny Album-** 100 coins."
			if c.save["coins"] >= 200:
				emojis.append('3️⃣')
				desc+= "\n3️⃣ **Flashy Album-** 200 coins."
			emojis.append('❌')
			desc+= "\n❌ **Don't buy.**"
			embed= (
				c.StEmbed(title="Album Shop", description= desc)
				.set_footer(f'{c.save["coins"]} coins')
			)
			msg= await c.channel.send(embed= embed)
			choice= await react_count(ctx.app.rest, msg, emojis)
			# message to send
			txt= ""
			# modify according to choice
			if choice.emoji == '3️⃣':
				c.save["coins"]-= 200
				txt+= "Bought Flashy Album."
				# percentages
				chance= [40, 35, 25]
			elif choice.emoji == '2️⃣':
				c.save["coins"]-= 100
				txt+= "Bought Shiny Album."
				chance= [50, 35, 15]
			elif choice.emoji == '1️⃣':
				c.save["coins"]-= 50
				txt+= "Bought Normal Album."
				chance= [75, 20, 5]
			elif choice.emoji == '❌':
				txt+= "Bought nothing."
				chance= None
			# pick random stickers
			if chance:
				for num in range(c.save["player"]["FP"]):
					x= random.choices(range(3), chance)[0]
					move= random.choice(list(rMoves[x]))
					self.add_sticker(move)
				# save coin amount to db
				sql_tools.saveID(ctx.guild_id, c.save)
		else:
			txt= "Not enough coins to buy from the album shop!"
		await c.channel.send(txt)

# defines enemies in battle
class Enemy(Being):
	def __init__(self, id: int):
		obj= c.battle["enemies"][id]
		super().__init__(obj, c.battle["enemies"]["names"][id])
		# the Enemy's id
		self.id= id
		# spiny is a bool that determines whether the player can jump on the enemy(True= No, False= Yes).
		self.spiny= obj['spiny']
		# flying is a bool that determines whether the player can hammer the enemy(True= No, False= Yes).
		self.flying= obj['flying']

# reaction with id
class Reactionish(hikari.Reaction):
	def __init__(self):
		self.count= 0
		self.emoji= None
		self.is_me= False
		self.id= 0
	# parse from hikari.Reaction
	@classmethod
	def parse(cls, obj: hikari.Reaction, custom_id: int= 0):
		instance= cls()
		instance.count= obj.count
		instance.emoji= obj.emoji
		instance.is_me= obj.is_me
		instance.id= custom_id
		return instance

# count reactions
async def react_count(rest: hikari.impl.RESTClientImpl, message: hikari.Message, emojis):
	# add emoji reactions
	for emoji in emojis:
		await rest.add_reaction(message= message, channel= c.channel, emoji= hikari.Emoji.parse(emoji))
	# set end time
	end_time= time.time() + 30
	max= Reactionish()
	while end_time > time.time():
		# update message info
		message= await c.channel.fetch_message(message)
		for i, reaction in enumerate(message.reactions):
			# change chosen reaction
			if reaction.count > max.count:
				max= Reactionish.parse(reaction, i)
			# if chosen reaction by 75% of participating members
			if max.count-1 >= c.members*0.75:
				return max
		time.sleep(1)
	return max

# group moves from c.moves by rarity
def group_rare() -> list[dict]:
	moves= [{}, {}, {}]
	for i in range(len(c.moves)-1):
		for j, k in enumerate(["Normal", "Shiny", "Flashy"]):
			if c.moves[i]["rarity"] == k:
				moves[j].update({i: c.moves[i]})
	return moves

# get random sticker through normal odds
async def random_sticker(player: Player, moves: list[int]) -> bool:
	if player.FP == 0:
		return False
	x= random.choices(range(3), [75, 20, 5])[0]
	id= random.choice(list(moves[x]))
	player.add_sticker(id)
	await c.channel.send(c.StEmbed(description= f"**+1 {c.moves[id]['icon']}{c.moves['names'][id]}**"))
	time.sleep(1)
	return True

# condition check and result execution
async def cond_check(ctx: lightbulb.Context, turn: int, lineup: list[Being], enemies: list[int], player: int):
	for phase in range(len(c.battle['phases'])-1):
		met= 0
		conditions= c.battle["phases"]["names"][phase].replace(" ", "")
		for orcondition in conditions.split("|"):
			orconditions= orcondition.split("&")
			# truthy result found using divisor
			divisor= len(orconditions)
			for condition in orconditions:
				# start of battle condition
				if condition.lower() == "start":
					if not enemies:
						met+= 1/divisor
				# turn condition
				elif re.findall(r"^[tT](?>[+]\d+|\d+)", condition):
					comp= int(re.findall(r'\d+', condition)[0])
					if comp == turn:
						met+= 1/divisor
					elif re.findall(r'+', condition)[0]:
						if turn % comp == 0:
							met+= 1/divisor
				# enemy @ stat condition
				elif re.findall(r"(?i:^e\d(?>[<>]=|[=<>])(?>\d{1,2})(?>hp|fp|pow|def|speed|stache))", condition):
					# numbers [enemy id and stat no.]
					nums= re.findall(r'\d+', condition)
					for guy in lineup:
						if hasattr(guy, "id"):
							if guy.id == int(nums[0])-1:
								# the selected stat
								stat= int(getattr(guy, re.findall(r'\D+$', condition)[0].upper()))
								break
							else:
								stat= None
					if stat:
						operand= re.findall(r'[<>]=|[=<>]', condition)[0]
						# set check
						if operand == "=":
							check = bool(stat == int(nums[1]))
						elif operand == ">":
							check = bool(stat > int(nums[1]))
						elif operand == "<":
							check = bool(stat < int(nums[1]))
						elif operand == ">=":
							check = bool(stat >= int(nums[1]))
						elif operand == "<=":
							check = bool(stat <= int(nums[1]))
						# check if true
						if check:
							met+= 1/divisor
			met= bool(math.floor(met))
			if met:
				break
		if met:
			results= c.battle["phases"][phase].split("&")
			for result in results:
				# every result except sys uses wResult
				wResult= result.replace(" ", "")
				# win event
				if wResult == "win":
					c.win= True
				# lose event
				elif wResult == "lose":
					c.lose= True
				# execute move
				elif re.findall(r'(?i:^move:)(?>(?>(?>\d{1,2})(?>,\d){5,6})|(?>\d,\d))(?!.+)', wResult):
					data= re.findall(r'(?i:(?<=^move:)).*', wResult)[0].split(',')
					if len(data) == 2:
						# format: [enemy index],[move index]
						info= c.battle["enemies"][int(data[0])]["moves"][int(data[1])]
						name= c.battle["enemies"][int(data[0])]["moves"]["names"][int(data[1])]
						# set move target
						target= player
					else:
						# format: [amount(2 digits)],[hits(1 digit)],[type(0/1/2)],[offense(0/1)],[stat(0/1/2/3/4/5)],[target(0/1/2)],(optional)[enemy index]
						info= {}
						name= None
						info['amount']= data[0]
						info['hits']= data[1]
						info['type']= num_to_list(data[2], ["Ground", "Aerial", "Magic"])
						info['offense']= bool(data[3])
						info['stat']= num_to_list(data[4], ["HP", "FP", "POW", "DEF", "SPEED", "STACHE"])
						info['target']= num_to_list(data[5], ["One", "All", "Random"])
						# set move target
						if info['target'] == "All":
							target= []
							for i in enemies:
								target.append(lineup[i])
						elif info['target'] == "One":
							index= data[6]
							target= [lineup[enemies[index]]]
						else:
							target= [lineup[random.choice(enemies)]]
					move= Action(name= name, obj= info)
					await move.deploy_action(target)
				# dialogue events
				elif re.findall(r'(?i:^event)\d', wResult):
					webhook= None
					dialogue= c.battle["dialogue"]
					event= dialogue["events"][int(re.findall(r'\d', wResult)[0])-1]
					for line in event:
						if not webhook:
							# check if webhook can be fetched, if not- create webhook
							try:
								webhook= await ctx.app.rest.fetch_webhook(c.save.get("webhook"))
							except:
								webhook= await ctx.app.rest.create_webhook(channel= c.save["channel"], name= "Starlow")
								# save webhook id to database
								c.save["webhook"]= webhook.webhook_id
								sql_tools.saveID(ctx.guild_id, c.save)
						await webhook.edit(name= dialogue["chars"]["names"][int(line[0])-1], avatar= dialogue["chars"][int(line[0])-1])
						await ctx.app.rest.execute_webhook(webhook, webhook.token, line[1])
					await webhook.edit(name= "Starlow")
					time.sleep(0.3)
				# system messages
				elif re.findall(r'(?i:^sys:).+', result):
					sys= re.findall(r'(?i:(?<=^sys:)).+', result)[0]
					await c.channel.send(sys)
				# spawn enemies
				elif re.findall(r'(?i:^spawn:)\d,\d', wResult):
					spawns= re.findall(r'(?i:(?<=^spawn:))\d,\d', result)[0].split("&")
					for spawn in spawns:
						i= spawn.split(",")
						for j in range(int(i[1])):
							enemy= Enemy(int(i[0])-1)
							lineup.append(enemy)

# manages turn events and order
async def turn_order(ctx: lightbulb.Context):
	turn= 1
	# moves grouped by rarity
	rMoves= group_rare()
	# player data
	pData= Player(name= c.save["player"]["name"], obj= c.save["player"])
	await pData.sticker_roulette(ctx, rMoves)
	# player/enemy lineup
	lineup= [pData, ]
	await c.channel.send(c.StEmbed(title= "B A T T L E  S T A R T !"))
	# player/enemy indexes
	player= 0
	enemies= []
	# initial condition check
	await cond_check(ctx, turn, lineup, enemies, player)
	# battle loop
	while not c.win and not c.lose:
		# speed check, reset player/enemy indexes
		enemies= []
		max= 0
		for i, guy in enumerate(lineup):
			if int(guy.SPEED) > max:
				lineup.remove(guy)
				lineup.insert(0, guy)
				max= int(guy.SPEED)
			if guy.__class__.__name__ == "Enemy":
				enemies.append(i)
			elif guy.__class__.__name__ == "Player":
				player= i
		# block check
		didnt_block= True
		# player/enemy turns
		for guy in lineup:
			one_more= True
			while one_more:
				one_more= False
				if guy.__class__.__name__ == "Player":
					# setting up embed and reactions
					emojis= ['<:st_jump:1136186635839623268>', '<:st_hammer:1136186760041336893>']
					# enemy info
					etext= ""
					for i in enemies:
						enemy= lineup[i]
						etext+= f"**{enemy.name}**"
						if not c.save["hideHP"]:
							etext+=f" | {enemy.HP}/{enemy.maxHP} HP"
						if i != len(enemies):
							etext+= "\n"
					desc= f"♥{guy.HP}/{guy.maxHP} HP\n{etext}\n\nWhat will you do?\n{emojis[0]} **Jump**\n{emojis[1]} **Hammer**"
					if guy.moves:
						emojis.append("📖")
						desc+= "\n📖 **Stickers**"
					if not guy.FP == 0 and c.save['coins'] >= 15:
						emojis.append("🎰")
						desc+= "\n🎰 **Battle Spinner** (15 coins)"
					# show inventory
					icons= ""
					for id, num in guy.moves.items():
						for j in range(num):
							icons+= c.moves[id]["icon"]
					if guy.moves:
						desc+= f"\n\n> Inventory({guy.maxFP-guy.FP}/{guy.maxFP}): {icons}"
					embed= (
						c.StEmbed(title= f"{guy.name}'s Turn!", description= desc)
						.set_footer(f"{c.save['coins']} coins")
					)
					msg= await c.channel.send(embed)
					one= await react_count(ctx.app.rest, msg, emojis)
					# jump or hammer
					if one.id == 0 or one.id == 1:
						# if jump, else hammer
						if one.id == 0:
							name= 'Jump'
						else:
							name= 'Hammer'
						# get basic move path
						path= os.path.abspath(__file__).replace(r"\btl_logic.py", r"\templates\basic.json")
						with open(path) as f:
							move= Action(jsonStr(f.read())[one.id], name)
					# sticker album
					elif one.emoji == '📖':
						# set sticker prompt
						desc= f"{guy.maxFP-guy.FP}/{guy.maxFP} stickers.\n"
						emojis= []
						for id, num in guy.moves.items():
							desc+= f"\n**{c.moves[id]['icon']} {c.moves['names'][id]} x{num}** | {c.moves[id]['info']}"
							emojis.append(c.moves[id]['icon'])
						embed= c.StEmbed(title= "Sticker Album", description= desc)
						msg= await c.channel.send(embed)
						choice= await react_count(ctx.app.rest, msg, emojis)
						# fetch move
						key= list(guy.moves)[choice.id]
						move= Action(c.moves[key], c.moves["names"][key])
						# remove sticker
						guy.moves[key]-=1
						guy.FP+=1
						if guy.moves[key] == 0:
							guy.moves.pop(key)
					# battle spinner
					elif one.emoji == '🎰':
						# add 3 random stickers
						for i in range(3):
							fun= await random_sticker(guy, rMoves)
							if not fun:
								break
						# remove 15 coins
						c.save['coins']-= 15
						sql_tools.saveID(ctx.guild_id, c.save)
						one_more= True
						continue
					# target selection
					if move.offense:
						if len(enemies) > 1:
							if move.target == "One":
								em_num= ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
								emojis= []
								desc= ""
								for i, enemyI in enumerate(etext.split("\n")):
									emojis.append(em_num[i])
									desc+= f"{em_num[i]} {enemyI}\n"
								embed= c.StEmbed(title= "Select a target!", description= desc)
								msg= await c.channel.send(embed)
								two= await react_count(ctx.app.rest, msg, emojis)
								target= [lineup[enemies[two.id]]]
							elif move.target == "All":
								target= []
								for i in enemies:
									target.append(lineup[i])
							elif move.target == "Random":
								i= random.choice(enemies)
								target= [lineup[i]]
						else:
							target= [lineup[enemies[0]]]
					else:
						target= [guy]
					blocked= False
				elif guy.__class__.__name__ == "Enemy":
					if didnt_block:
						# block prompt
						embed= c.StEmbed(title= "Block the attack!", description= "React to this message to block enemies' attacks!")
						msg= await c.channel.send(embed)
						react= await react_count(ctx.app.rest, msg, ['🛡'])
						# check if valid
						if react.count > c.members*0.75:
							blocked= True
							if random.random() <= (25+50*(lineup[player].STACHE/100))/100:
								await random_sticker(lineup[player], rMoves)
						else:
							blocked= False
						didnt_block= False
					# select move
					if guy.moves:
						move= random.choice(guy.moves)
					# select target
					if move.offense:
						target= [lineup[player]]
					else:
						if move.target == "One" or move.target == "Random":
							i= random.choice(enemies)
							target= [lineup[i]]
						else:
							target= []
							for i in enemies:
								target.append(lineup[i])
				# initate action
				await move.deploy_action(target, guy, blocked)
				if random.random() == int(guy.SPEED)/100:
					one_more= True
					await c.channel.send(c.StEmbed(description= "One more!"))
			# rotating condition check
			await cond_check(ctx, turn, lineup, enemies, player)
			# check if 0 HP
			for person in target:
				if person.HP <= 0:
					if person.__class__.__name__ == "Player":
						c.lose= True
						break
					else:
						lineup.remove(person)
						if len(lineup) == 1:
							c.win= True
							break
						# enemy defeat bonus
						if random.random() == int(guy.STACHE)/100:
							choice= random.randrange(0, 3)
							if choice == 0:
								guy.HP= guy.maxHP
								txt= "HP Max"
							elif choice == 1:
								guy.POW+= 2
								txt= "POW Up"
							elif choice == 2:
								guy.DEF+= 2
								txt= "DEF Up"
							elif choice == 3:
								one_more= True
								txt= "One more"
							await c.channel.send(c.StEmbed(description= f"{txt}!"))
			# advance turn
			turn+=1/len(lineup)
	if c.win:
		await c.channel.send("You win!")
		time.sleep(0.3)
		# battle rewards
		if c.save['reward']['set'] == "Choice":
			# reward select prompt
			desc= ''
			emojis= []
			items= c.save['reward']['items']
			if 'HP' in items:
				emojis.append('♥')
				desc+= "♥ HP-Up Heart\n"
			if 'FP' in items:
				emojis.append('🌻')
				desc+= "🌻 FP-Up Flower\n"
			if 'SPEED' in items:
				emojis.append('👟')
				desc+= "👟 Speed-Up Soles\n"
			if 'STACHE' in items:
				emojis.append('💇‍♂️')
				desc+= f"💇‍♂️ Stache-Up Comb"
			embed= c.StEmbed(title="Select Reward!", description= desc)
			msg= await c.channel.send(embed)
			choice= await react_count(ctx.app.rest, msg, emojis)
			# get stat
			if choice.id == 0:
				stat= ['HP']
			elif choice.id == 1:
				stat= ['FP']
			elif choice.id == 2:
				stat= ['SPEED']
			elif choice.id == 3:
				stat= ['STACHE']
		elif c.save['reward']['set'] == "All":
			stat= c.save['reward']['items']
		else:
			stat= [random.choice(c.save['reward']['items'])]
		# set stat reward
		stat_txt= ''
		for item in stat:
			c.save['player'][item]+=5
			stat_txt+= f'+5 {item}.\n'
		# set coin reward
		coins= 0
		for i in range(len(c.battle['enemies'])-1):
			enemy= c.battle['enemies'][i]
			coins+= (int(enemy['HP'])+int(enemy['POW'])+int(enemy['DEF']))
		c.save['coins']+= coins
		# save to database
		sql_tools.saveID(ctx.guild_id, c.save)
		# send final message
		embed= (
			c.StEmbed(title= "Rewards:", description= f"{stat_txt}+{coins} coins.")
			.set_footer("See you next time!")
		)
		await c.channel.send(embed)
	elif c.lose:
		await c.channel.send("You lose.")
	# reset global values
	c.moves = {}
	c.win= False
	c.lose= False