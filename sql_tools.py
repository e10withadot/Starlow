import sqlite3
import json
import os
from slipper import jsonStr

# stores Starlow data into an sqlite database file
class StDbAccess():
	def __init__(self, filename: str= None):
		self.path= filename

	def connect(self):
		self.conn = sqlite3.connect(self.path)
		self.conn.execute("CREATE TABLE IF NOT EXISTS server_data (guild_id numeric unique, settings text, b0 text, b1 text, b2 text, b3 text, b4 text)")

	def close(self):
		self.conn.commit()
		self.conn.close()

	def get1(self, id: str):
		item = self.conn.execute(f'SELECT settings FROM server_data WHERE guild_id = ?', (id,)).fetchone()
		self.close()
		if item[0]:
			return jsonStr(item[0])
		return None
	
	def get2(self, id: str):
		items= []
		columns= ["b0", "b1", "b2", "b3", "b4"]
		for column in columns:
			item= self.conn.execute(f'SELECT {column} FROM server_data WHERE guild_id = ?', (id,)).fetchone()
			if item[0]:
				items.append(jsonStr(item[0]))
			else:
				items.append(None)
		self.close()
		return items
	
	def set1(self, id: str, obj):
		self.conn.execute('INSERT OR IGNORE INTO server_data (guild_id) VALUES (?)', (id,))
		self.conn.execute('UPDATE server_data SET settings=? WHERE guild_id=?', (obj, id))
		self.close()
		
	def set2(self, id: str, obj, index: int= 0):
		self.conn.execute(f'UPDATE server_data SET b{index}=? WHERE guild_id=?', (obj, id))
		self.close()

PATH= os.path.abspath(__file__).replace("sql_tools.py", "server_data.db")
# initialize database
db = StDbAccess(PATH)

# save data to guild id
def saveID(guildID: str, data: dict, set: bool= True, i: int= 0):
	global db
	db.connect()
	if set:
		db.set1(guildID, json.dumps(data))
	else:
		db.set2(guildID, json.dumps(data), i)
	print(data)
	
# load data from guild id
def loadID(guildID: str, set: bool= True) -> dict | None:
	global db
	db.connect()
	if set:
		data = db.get1(guildID)
	else:
		data = db.get2(guildID)
	if data:
		return data
	else:
		return None

# is /luigi enabled?
def isLuigi(guildID: str) -> bool:
	global db
	db.connect(PATH)
	settings = db.get1(guildID)
	return settings.get("luigi")