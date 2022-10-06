import sys
import os
import re

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spidermisslewares.httperror import HttpError

from fileutil import create_filepath, remove_files_recursively

ERRORS = []

# our main collections 
songs_by_artist = {}
songs_by_year = {}

yearend_table_wiki_selector = 'table.wikitable'

class PopSpider(scrapy.Spider):

	def get_wiki_url(year):
		return 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_{0}'.format(year)

	def start_requests(self):
		"""Scrape all pages from Wikipedia and register post-response callbacks"""
		for year in range(1959, 2022):
			yield scrapy.Request(url=get_wiki_url(year), callback=self.process_response, errback=self.errback)
			
	def errback(self):
		"""Handles error responses"""
		request_url = failure.request.url
		if failure.check(HttpError):
			response = failure.value.response
			ERRORS.append('HttpError on {0}: http status = {1}'.format(request_url, response.status))
		else:
			ERRORS.append('Unknown error on {0}'.format(request_url))

	def process_response(self, response):
		year = re.search(r'\d+$', response.url)
		for wikitable in response.css(yearend_table_wiki_selector).extract():
			if re.search(r'Year\-End', wikitable):
				write_output(year, wikitable)

	def write_output(self, year, text):
		filepath = 'output'
		if create_filepath(filepath):
			remove_files_recursively(filepath)

		raw_filename = os.path.join(filepath, '{0}.txt'.format(year))
		with open(raw_filename, 'w') as f:
			f.write(text)


def main():
	"""Main entry point from external process or script"""
	process = CrawlerProcess({
		'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})
	process.crawl(PopSpider)
	# the script will block at start() until the crawling is finished
	process.start()

	# print errors to stdout (and flush buffer) after script has finished running
	for error_line in ERRORS:
		print('pop-spider ERROR: {0}'.format(error_line))

	sys.stdout.flush()

	# return 0 if script ran successfully, nonzero if errors.
	# Shell variable "$?" will capture this value.
	sys.exit(len(ERRORS))


if __name__ == '__main__':
	# default main when running from shell script
	main()
