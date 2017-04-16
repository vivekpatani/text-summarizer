#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============== Imports ==============
from nltk.tokenize import sent_tokenize
import requests, json
from subprocess import call
from time import time

# ========== Read/Write File Calls ===========
def readfile(file_name, folder_location):
	"""
	Reads the file and returns a single
	string.
	"""
	try:
		with open(folder_location + file_name, encoding='utf-8') as f:
			data = f.read().rstrip()
		return data
	except IOError:
		print('No File Found.')

def dump(data, file_name, folder_location):
	"""
	Dumps a string to a file
	"""
	try:
		with open(folder_location + file_name, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=4)
	except IOError:
		print("Error Dumping File")

# ================== Manipulate Information ========
def extract_information(data):
	"""
	Extracting relevant dependencies
	"""
	information = {}
	sentence_data = data["sentences"]
	for each_sentence in sentence_data:
		print(each_sentence["index"])
		dependencies = each_sentence["enhancedPlusPlusDependencies"]
		for each_dep in dependencies:
			print(each_dep["dependentGloss"] + ": " + each_dep["dep"])

# ============= Main Call ==============
def main():
	"""
	Main Calls the rolling function
	"""
	file_data = readfile('input.txt',folder_location='./input/')

	if (file_data != None):
		start = time()
		params = (('properties', '{"timeout":50000, "annotators":"tokenize,ssplit,pos,depparse","outputFormat":"json"}'),)
		response = requests.post('http://localhost:8081/', params=params, data=file_data)
		end = time()
		data = json.loads(response.text)
		dump(data, 'output.txt.json', './output/')
		extract_information(data)
		print(end - start)

# ========= Boiler Plate Code ==========
if __name__ == "__main__":
	main()