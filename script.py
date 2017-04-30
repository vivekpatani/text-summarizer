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
	'''
	Reads the file and returns a single
	string.
	'''
	try:
		with open(folder_location + file_name, encoding='utf-8') as f:
			data = f.read().rstrip()
		return data
	except IOError:
		print('No File Found.')

def dump(data, file_name, folder_location):
	'''
	Dumps a string to a file
	'''
	try:
		with open(folder_location + file_name, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=4)
			print('File Dumping Successful')
	except IOError:
		print('Error Dumping File')

# ================== Manipulate Information ==============

# ================= Resolve Anaphora =====================

def resolve_anaphoras(data):
	'''
	Extract all the anaphoras.
	'''
	refs = {}
	data = data['corefs']
	for ref in data:
		# Non representatives are items which itself do not represent
		# an entity, but are linked.
		non_reps = set()
		key = ''
		for sub_ref in data[ref]:
			if (sub_ref['isRepresentativeMention']):
				key = sub_ref['text']
			else:
				non_reps.add(((int(sub_ref['sentNum']) - 1), int(sub_ref['startIndex'] - 1), sub_ref['text']))

		if (key in refs):
			non_reps_exist = refs[key]
			non_reps_exist.union(non_reps)
			refs[key] = non_reps_exist
		else: refs[key] = non_reps

	return refs

def update_anaphoras(file_data, data):
	'''
	Generates a new interim file,
	with resolved anaphora.
	'''
	for anaphora in data:
		for each_dep in data[anaphora]:
			flag = True
			sentence = file_data[each_dep[0]].split()
			word_idx = each_dep[1]
			word = each_dep[2]
			if (sentence[word_idx] == word):
				sentence[word_idx] = anaphora

			elif (word_idx - 1 >= 0 and sentence[word_idx - 1] == word):
				sentence[word_idx - 1] = anaphora

			elif (word_idx + 1 < len(sentence) and sentence[word_idx + 1] == word):
				sentence[word_idx + 1] = anaphora

			else: flag = False

			if (flag):
				joined_s = ' '.join(sentence)
				file_data[each_dep[0]] = joined_s

	return ' '.join(file_data)

# ================= Dependency Resolution ================
def extract_information(data):
	'''
	Pivot function to extract information.
	'''
	tags = extract_sentence(data['sentences'])
	# print(tags)

def extract_sentence(data):
	'''
	Extracting relevant dependencies
	'''
	information = {}
	for each_sentence in data:
		idx = each_sentence['index']
		information[idx] = {}
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
	'''
	Extracts Deep Relations
	'''
	properties = set(['ROOT', 'nsubj', 'nobj', 'dsubj', 'dobj'])
	if (dep == 'compound'):
		g_dict[gloss] = gloss + ' ' + data['governorGloss']

	if (dep in properties):
		return gloss, dep
	else: return None,None 

# ============= Main Call ==============
def main():
	'''
	Main Calls the rolling function
	'''
	file_data = readfile('input.txt',folder_location='./input/')

	if (file_data != None):
		start = time()

		# First Resolve Anaphoras
		anaphoras = (('properties', '{"timeout":50000, "annotators":"ssplit,coref","outputFormat":"json"}'),)
		response = requests.post('http://localhost:8081/', params=anaphoras, data=file_data)
		data = json.loads(response.text)
		dump(data, 'intermediate.txt.json', './output/')
		extracted_anaphoras = resolve_anaphoras(data)
		sent_tokenize_list = sent_tokenize(file_data)
		update_input = update_anaphoras(sent_tokenize_list, extracted_anaphoras)

		# Store Dependencies in SQL
		params = (('properties', '{"timeout":50000, "annotators":"tokenize,ssplit,lemma,parse,mention","outputFormat":"json"}'),)
		response = requests.post('http://localhost:8081/', params=params, data=update_input)
		end = time()
		data = json.loads(response.text)
		dump(data, 'output.txt.json', './output/')
		extract_information(data)
		print(end - start)

# ========= Boiler Plate Code ==========
if __name__ == '__main__':
	main()