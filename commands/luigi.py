import hikari
import lightbulb
import random
import sql_tools

plugin = lightbulb.Plugin("luigi")
@plugin.command
@lightbulb.command("luigi", "Starlow’s opinion on Luigi. (May include vulgar language)")
@lightbulb.implements(lightbulb.SlashCommand)
async def luigi(ctx: lightbulb.Context) -> None:
	if sql_tools.isLuigi(str(ctx.guild_id)):
		responses = [
		"i fucking despise luigi",
		"Mario >>>>>>>>>>>>>>>>>>> Luigi",
		"You know why the Year of Luigi was a failure? That was a trick question.",
		"I hate Luigi’s Mansion for the GameCube. Everyone who likes it is annoying",
		"Luigi? More like *Poo*igi.",
		"luigi sucks",
		"i wish luigi would burn alive",
		"i want to curb stomp luigi",
		"Little pissy baby pussy boy",
		"Did you know that Luigi is actually the 34th character in Sonic R? Search 'Luigi R34' to learn more!",
		"Did you know that Luigi once beat Bowser so hard, the impact created a crater in the shape of an X? Search 'Luigi X Bowser' to learn more!",
		"There’s a reason Luigi has an L on his cap.",
		"Dream Team is a great game! I get to torture Luigi in it",
		"Luigi is a worthless, bitch ass. His life literally is as valuable as a summer ant. I'm just gonna stomp him and he’s gonna keep coming back, imma seal up all my cracks, he’s gonna keep coming back. Why? Cause he smellin the syrup. Worthless bitch ass.\nHe gonna stay on me until he dies. He serves no purpose in life. His purpose in life is to be on my stream sucking on me daily. Your purpose in life is to be in that chat blowing daily.\nYour life is nothing, you serve zero purpose.\nYou should kill yourself, NOW.\nAnd give somebody else a piece of that oxygen, and ozone layer, that's covered up so that we can breathe inside this blue trapped bubble.\nCause what are you here for? To worship me? Kill yourself. I mean that, with a 100%, with a 1000%. I've never seen somebody so worthless in my life. I'm deadass. I've not seen such a more worthless bitch ass, in my life.",
		"If he has kids? Oh my god, Imagine if a person like that has kids. Like imagine. Imagine if somebody like that actually has kids. I would feel so sorry for his children cause the guy literally serves no fucking purpose.\nImagine a father, now we got lots of people with, wives and kids and shit that suck me daily on the internet. But imagine if this guy actually had children. This guy is devoting the time he could be spending with his kids, checking out a star sprite on stream, cucking over her relentlessly. It's crazy.",
		"I've never seen someone so relentless to be seen. Somebody, somebody, somebody's value so worthless that they'll come into a fucking stream, and keep coming in this bitch over and over and over and over and over and over again. We keep banning him. (Talking to Luigi) Dude let me, let me, let's do you a favor.\nLet's go to the 99-cent store, let's pick out a rope together. I'm gonna give you an assisted suicide. Let's pick out a rope together right, and we're gonna take all the greatest troll clips, put a TV screen right in front of you. Im gonna hang that rope on top of the motherfucking garage.\nWe're gonna force feed you. Pry your eyes open. Probably dont need to do that cause you're already on me daily. We're gonna pry your eyes open, until you consistenly watch clips over and over and over and over and over again. Till you're gonna be like \"oh this is fucking torture\". You're gonna start going crazy, you're gonna start feeling crazy. Just, your eyes are gonna bleed, the retinas are gonna just start pouring out, pouring out blood and crack open veins, and the reitnas are just going to start engaging and bulging.\nThen im gonna grab that rope and say are you ready? And you're gonna say yes and im just gonna PULL IT. While you BEG me, BEG me and I mean BEG me to kill you. And choke you, choke the worthless life out of your sorry ass."
		]
		await ctx.respond(random.choice(responses))
	else: 
		embed = hikari.Embed(title="This command was disabled by the server.", color=0xFF0000)
		await ctx.respond(embed=embed)

def load(bot):
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)