# -*- coding: utf-8 -*-
import re
import time
import socket
from github import Github, GithubException
from jinja2 import utils

# https://developer.github.com/v3/#pagination
# max 5000 requests/H
per_page = 50
repos = []
repos_count = 0

class Engine(object):
	def __init__(self, token):
		self.token = token
		self.g = Github(login_or_token=token, per_page=per_page)
		self.rules = None
		self.code = ''
		self.full_name = ''
		self.url = ''
		self.path = ''
		self.result = {}
		self.ext = None
		self.keywords = None

	def process_pages(self, pages_content, page, total):
		if self.rules['mode'] == '0':
			for index, content in enumerate(pages_content):
				#time.sleep(0.5)
				current_i = page * per_page + index
				base_info = '[{current}/{count}]'.format(current=current_i, count=total)

				self.url = content.html_url
				self.path = content.path
				self.full_name = content.repository.full_name.strip()
				try:
					self.code = content.decoded_content.decode('utf-8')
				except Exception as e:
					print('Get Content Exception: {e} retrying...'.format(e=e))
					continue

				match_codes = self.find_keywords_lines()
				if len(match_codes) == 0:
					#print('{b} Did not find keywords lines, skip!'.format(b=base_info))
					continue

				result = {
					'url': self.url,
					'match_codes': match_codes,
					'repository': self.full_name,
					'path': self.path,
				}
				self.result[current_i] = result
				print('{b} Find keywords lines, the next one!'.format(b=base_info))

		elif self.rules['mode'] == '1':
			global repos
			for index, content in enumerate(pages_content):
				current_i = page * per_page + index
				base_info = '[{current}/{count}]'.format(current=current_i, count=total)

				self.url = content.html_url
				self.path = content.path
				self.full_name = content.repository.full_name.strip()
		
				try:
					self.code = content.decoded_content.decode('utf-8')
				except Exception as e:
					print('Get Content Exception: {e} retrying...'.format(e=e))
					continue
				for i in self.rules['repos']['features']:
					if i in self.code and self.full_name not in repos:
						repos.append(self.full_name)
						print('Find repos https://github.com/' + self.full_name + ', the next one!')
						break;
		
		return True


	def search(self, keywords, rules):
		if rules['mode'] == '0':
			self.ext = rules['corp']['ext']
		elif rules['mode'] == '1':
			self.ext = rules['repos']['ext']

		self.keywords = keywords
		self.rules = rules
		try:
			rate_limiting = self.g.rate_limiting
			rate_limiting_reset_time = self.g.rate_limiting_resettime

			ext_query = ''
			if self.ext is not None:
				for ext in self.ext.split(','):
					ext_query += ' extension:' + str(ext)
			keyword = self.keywords + ext_query
			print("search for " + keyword)
			resource = self.g.search_code(keyword, sort="indexed", order="desc")
		except GithubException as e:
			print('GitHub [search_code] exception(code: {c} msg: {m}'.format(c=e.status, m=e.data))
			time.sleep(10)
			return False

		try:
			total = resource.totalCount
			print('[{k}] The actual number: {count}'.format(k=self.keywords, count=total))
		except socket.timeout as e:
			print(str(e))
			return False
		except GithubException as e:
			print('GitHub [search_code] exception(code: {c} msg: {m}'.format(c=e.status, m=e.data))
			time.sleep(10)
			return False

		pages = total // 50
		if total % 50 != 0:
			pages = pages + 1
		if pages > 20:
			pages = 20

		for page in range(pages):
			try:
				pages_content = resource.get_page(page)
			except socket.timeout:
				print(('[{k}] [get_page] Time out, skip to get the next page！'.format(k=self.keywords)))
				continue
			except GithubException as e:
				print('GitHub [get_page] exception(code: {c} msg: {m}'.format(c=e.status, m=e.data))
				time.sleep(10)
				return False

			self.process_pages(pages_content, page, total)
			self.save_result(self.rules['corp']['proname'])
		return True


	def find_keywords_lines(self):
		self.code = self.code.replace('<img', '')
		lines = self.code.splitlines()
		match_codes = {}
        
		for line in lines:
			for key,value in self.rules['keys'].items():
				if key not in match_codes:
					match_codes[key] = ''
				if re.findall(value, line.lower()):
					match_codes[key] += line + '|'

		return match_codes


	def save_result(self, name):
		if self.rules['mode'] == '0':
			if len(self.result) == 0:
				print('none content for save.')
				return

			html = '<h3>Rule: {rule_regex} Count: {count} Datetime: {datetime}</h3>'.format(rule_regex=self.keywords, datetime=time.strftime("%Y-%m-%d %H:%M:%S"), count=len(self.result))
			for i, v in self.result.items():
				html += '<h3>({i})<a href="{url}">detail</a> {repository}/{path}</h3>'.format(i=i, url=v['url'], repository=v['repository'], path=v['path'])
				if len(v['match_codes']) > 0:
					code = ''
					for k,c in v['match_codes'].items():
						code += '<b>' + k + ':</b><br>'
						for j in c.split('|'):
							code += '&emsp;&emsp;&emsp;&emsp;{j}<br>'.format(j=utils.escape(j))
					html += '<code>{code}</code><hr>'.format(code=code)
			html += '</table></body>'
		
			f = open('report/' + name + '.html', 'a')
			f.write(html)
			f.close()
		elif self.rules['mode'] == '1':
			global repos_count,repos
			if not repos:
				return
			f = open('report/repos.html', 'a')
			repos.sort()

			for i in repos:
				repos_count += 1
				f.write(str(repos_count) + ':<a href=https://github.com/' + i + '>' + i + '</a>&emsp;&emsp;&emsp;&emsp;author:' + i.split('/')[0] + '<br>')
			f.close()
