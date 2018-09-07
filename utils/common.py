#!/usr/bin/python

import os
import json

def save_data(filename, data):
	fd = open(filename, 'w')
	json.dump(data, fd, indent=4, ensure_ascii=False)
	fd.close()


def read_data(filename):
	if os.path.exists(filename):
		try:
			fd = open(filename, 'r')
			data = json.load(fd)
			return data
		finally:
			fd.close()
	else:
		return []
