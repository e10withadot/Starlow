'''
Generic Python functions
'''
import json
import re

def boolTerm(bool: bool) -> str:
	'''
	'True'= 'On', 'False'= 'Off'
	'''
	if bool:
		return "On"
	return "Off"

def jsonStr(obj) -> dict:
	'''
	Converts int keys from String to int.
	'''
	if not isinstance(obj, dict):
		obj= json.loads(obj)
	nObj= {}
	for key, value in obj.items():
		if re.findall(r"\d+", key):
			nKey= int(key)
		else:
			nKey= key
		if isinstance(value, dict):
			nObj[nKey]= jsonStr(value)
		else:
			nObj[nKey]= value
	return nObj