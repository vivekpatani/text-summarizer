#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============== Imports ==============
from subprocess import call

# =============== Init Server Python ================
def terminate():
	"""
	Stops and removes Docker container.
	"""
	call(['docker', 'stop', 'corenlp-server'])
	call(['docker', 'rm', 'corenlp-server'])
	print("Server Successfully Terminated..")

def main():
	"""
	Main call.
	"""
	terminate()

# ============ Boiler Plate ==================
if __name__ == '__main__':
	main()