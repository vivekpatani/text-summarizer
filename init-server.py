#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============== Imports ==============
from subprocess import call

# =============== Init Server Python ================
def init():
	"""
	Initiates Docker container
	"""
	call(['docker', 'run', '-d', '-p', '8081:80', '--log-opt', 'max-file=8', '--log-opt', 'max-size=8m', '--name', 'corenlp-server', 'corenlp-server'])
	print("Server Initialisation Successful..\nPlease send out your requests to 8081..\n")

def main():
	"""
	Main call
	"""
	init()

# ============ Boiler Plate ==================
if __name__ == '__main__':
	main()