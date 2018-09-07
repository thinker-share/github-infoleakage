#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    github-infoleakage

    :author:    thinker-share
    :homepage:  https://github.com/thinker-share
"""

import os
import sys
import time
import optparse

import utils.engine as engine
import utils.common as common

def search_pages(rules):
	if rules['mode'] == '0':
		print('start search code.')
		for i in rules['corp']['keywords'].split('|'):
			engine.Engine(token=rules['token']).search(keywords=i, rules=rules)
			time.sleep(10)

	elif rules['mode'] == '1':
		print('start search repos.')
		for i in rules['repos']['keywords'].split('|'):
			engine.Engine(token=rules['token']).search(keywords=i, rules=rules)
			time.sleep(10)

		# search leakage from repos.
		repos = engine.get_repos()
		for i in repos:
			for k in ['user','pass']:
				engine.Engine(token=rules['token']).search(keywords=k, rules=rules, repos=i)
				time.sleep(10)
	

def init_opt():
	parser = optparse.OptionParser('usage: ./%prog [options] \n'
									'Example:\n' 
									'		./scan.py -f rule.json')
	parser.add_option('-f', '--file', dest='rfile', default='rule.json', type='string', help='rules config file.')
	parser.add_option('-m', '--mode', dest='mode', default='0', type='string', help='scan mode, 0:code, 1:repos')
	(options, args) = parser.parse_args()
	
	rules = common.read_data(options.rfile)
	if len(rules) == 0:
		print("no rule find, exit.")
		sys.exit(1)

	rules['mode'] = options.mode

	os.system('mkdir -p report')
	os.system("rm -f report/*")
	return rules

if __name__ == '__main__':
	rules = init_opt()	
	search_pages(rules)
