import json
import re
# generic Python library

# converts boolean terms to human speak
def boolTerm(bool: bool) -> str:
	if bool:
		return "On"
	return "Off"

# turns num keys from string to int
def jsonStr(obj) -> dict:
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

# takes number index and returns list element
def num_to_list(obj: int, list: list):
	for i, thing in enumerate(list):
		if int(obj) == i:
			return thing