#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============== Imports ==============
from nltk.tokenize import sent_tokenize

# ========== Read File Calls ===========
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
		print("No File Found.")

# ============= Main Call ==============
def main():
	"""
	Main Calls the rolling function
	"""
	data = readfile('input.txt',folder_location='./input/')

	if (data != None):
		sent_tokenize_list = sent_tokenize(data)
		for each_sentence in sent_tokenize_list:
			print(each_sentence)
		print(len(sent_tokenize_list))


# ========= Boiler Plate Code ==========
if __name__ == "__main__":
	main()