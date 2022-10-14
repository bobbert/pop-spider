import sys
import os
import re

import scrapy
from scrapy.crawler import CrawlerProcess

from fileutil import create_filepath, remove_files_recursively

ERRORS = []

# our main collections 
songs_by_artist = {}
songs_by_year = {}

yearend_table_wiki_selector = 'table.wikitable'

class YearEndListSpider(scrapy.Spider):
	name = 'yearendlists'

	def get_wiki_url(self, year):
		return 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_{0}'.format(year)

	def start_requests(self):
		"""Scrape all pages from Wikipedia and register post-response callbacks"""
		urls_by_year = {year: self.get_wiki_url(year) for year in range(1959, 2022)}

		for (year, url) in urls_by_year.items():
			yield scrapy.Request(url=url, callback=self.parse, errback=self.errback, cb_kwargs={'year': year })
			
	def errback(self):
		"""Handles error responses"""
		request_url = failure.request.url
		response = failure.value.response
		ERRORS.append('HTTP error on request URL {0}, status = {1}'.format(request_url, response.status))

	def parse(self, response, year):
		"""Parse HTML response retrieved from URL, with year attached""" 
		for wikitable in response.css(yearend_table_wiki_selector):
			for selected_row in wikitable.css('tr'):
				if (len(selected_row.css('td').getall()) >= 3):
					position = selected_row.css('td:first-child::text').get()
					artist_cell = selected_row.css('td:nth-child(2)')
					song_cell = selected_row.css('td:nth-child(3)')
					yield {
						'position': position,
						'artist': self.to_artist_or_song_displayed(artist_cell),
						'song': self.to_artist_or_song_displayed(song_cell),
						'year': year
					}


	def to_artist_or_song_displayed(self, selected_cell):
		"""Returns artist/song cell value to be displayed, as either plain text or hyperlink"""
		if selected_cell.css('a').get() is None:
			return selected_cell.css('::text').get()
		else:
			raw_url = selected_cell.css('a::attr(href)').get()
			name = selected_cell.css('a::text').get()
			return self.to_excel_hyperlink(raw_url, name)

	def to_excel_hyperlink(self, relative_url, name):
		url = self.resolve_wiki_links(relative_url)
		return '=HYPERLINK("{0}", "{1}")'.format(url, name)

	def resolve_wiki_links(self, text):
		return text.replace("/wiki/", "https://en.wikipedia.org/wiki/")


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
