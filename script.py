#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============== Imports ==============
from nltk.tokenize import sent_tokenize
import requests, json
from subprocess import call
from time import time
import copy

# ================ Globals ===================
g_dict = {}

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
			print('File Dumping Successful')
	except IOError:
		print('Error Dumping File')

# ================== Manipulate Information ========
def extract_information(data):

	corefernce = extract_references(data['corefs'])
	tags = extract_sentence(data['sentences'])
	print(tags)

def extract_references(data):
	"""
	Extract References
	"""
	refs = {}
	for ref in data:
		non_reps = set()
		k = ''
		for sub_ref in data[ref]:
			print(sub_ref['isRepresentativeMention'])
			if (sub_ref['isRepresentativeMention']):
				k = sub_ref['text']
			else:
				non_reps.add(int(sub_ref['startIndex']) - 1)

		if (k in refs):
			non_reps_exist = refs[k]
			non_reps_exist.union(non_reps)
			refs[k] = non_reps_exist
		else: refs[k] = non_reps

	return refs

def extract_sentence(data):
	"""
	Extracting relevant dependencies
	"""
	information = {}
	for each_sentence in data:
		idx = each_sentence['index']
		information[idx] = {}
		print(each_sentence['index'])
		dependencies = each_sentence['enhancedPlusPlusDependencies']
		for each_dep in dependencies:
			gloss, dep = extract_dep_information(each_dep['dependentGloss'], each_dep['dep'], each_dep)
			if (gloss != None and dep != None):
				print(gloss, dep)
				current_dep = []
				if (dep in information[idx]):
					current_dep = information[idx][dep]
					current_dep.append(gloss)
					information[idx][dep] = copy.deepcopy(current_dep)
				else:
					current_dep = [gloss]
					information[idx][dep] = copy.deepcopy(current_dep)
	print(g_dict)
	return information

def extract_dep_information(gloss, dep, data):
	"""
	Extracts Deep Relations
	"""
	properties = set(['ROOT', 'nsubj', 'nobj', 'dsubj', 'dobj'])
	if (dep == 'compound'):
		g_dict[gloss] = gloss + ' ' + data['governorGloss']

	if (dep in properties):
		return gloss, dep
	else: return None,None 

# ============= Main Call ==============
def main():
	"""
	Main Calls the rolling function
	"""
	file_data = readfile('input.txt',folder_location='./input/')

	if (file_data != None):
		start = time()
		params = (('properties', '{"timeout":50000, "annotators":"tokenize,ssplit,lemma,parse,mention,coref","outputFormat":"json"}'),)
		response = requests.post('http://localhost:8081/', params=params, data=file_data)
		end = time()
		data = json.loads(response.text)
		dump(data, 'output.txt.json', './output/')
		extract_information(data)
		print(end - start)

# ========= Boiler Plate Code ==========
if __name__ == '__main__':
	main()