import sys
import os
import re

import scrapy
from scrapy.crawler import CrawlerProcess
from threading import Lock

from fileutil import create_filepath, remove_files_recursively

ERRORS = []

# collection of original year for dupe resolution
# NOTE: responses aren't guaranteed to arrive ordered by year, and this 
# may not actually be the original year.
original_year_by_song = {}

yearend_table_wiki_selector = 'table.wikitable'

class YearEndListSpider(scrapy.Spider):
	name = 'yearendlists'
	lock = Lock()

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

					# rows should appear in wikitable as:
					# <tr>
					#   <td> rank # in year-end </td>
					#   <td> artist info (name and/or link) </td>
					#   <td> song info (name and/or link) </td>
					# </tr>

					artist_cell_value = self.to_artist_or_song_displayed(selected_row.css('td:nth-child(2)'))
					song_cell_value = self.to_artist_or_song_displayed(selected_row.css('td:nth-child(3)'))
					song_artist_key = '|'.join([artist_cell_value, song_cell_value])

					yield {
						'position': selected_row.css('td:first-child::text').get(),
						'artist': artist_cell_value,
						'song': song_cell_value,
						'year': self.get_resolved_year(song_artist_key, year)
					}


	def song_name_key(self, selected_cell):
		"""Returns artist cell value as key to be referenced"""
		if selected_cell.css('a').get() is None:
			return selected_cell.css('::text').get().strip()
		else:
			return selected_cell.css('a::attr(href)').get()

	def to_artist_or_song_displayed(self, selected_cell):
		"""Returns artist/song cell value to be displayed, as either plain text or hyperlink"""
		text_nodes = [textnode.get() for textnode in selected_cell.css('::text')]
		excel_hyperlinks = [self.link_node_to_excel_hyperlink(node) for node in selected_cell.css('a')]

		result_text = ""
		larger_len = max(len(text_nodes), len(excel_hyperlinks))
		for i in range(larger_len):
			if i < len(text_nodes):
				result_text += text_nodes[i]
			else:
				result_text += " "

			if i < len(excel_hyperlinks):
				result_text += excel_hyperlinks[i]

		return result_text

	def link_node_to_excel_hyperlink(self, link_node):
		raw_url = link_node.css('::attr(href)').get()
		name = link_node.css('::text').get().strip()
		return self.url_to_excel_hyperlink(raw_url, name)

	def url_to_excel_hyperlink(self, relative_url, name):
		url = self.resolve_wiki_links(relative_url)
		return '=HYPERLINK("{0}", "{1}")'.format(url, name)

	def resolve_wiki_links(self, text):
		return text.replace("/wiki/", "https://en.wikipedia.org/wiki/")

	def get_resolved_year(self, song_artist_key, year):
		"""Check year lookup dictonary for previously instances of same song"""
		try:
			# parse() runs on a different thread for each year's URL response.
			# all lookups on original_year_by_song need to be thread-safe.
			self.lock.acquire()
			if song_artist_key in original_year_by_song:
				original_year = original_year_by_song[song_artist_key]
				if year > original_year:
					return '{0} ({1})'.format(year, original_year)
				elif year < original_year:
					return '{0} ({1}) ***'.format(year, original_year)
				else:
					return year
			else:
				original_year_by_song[song_artist_key] = year
				return year

		finally:
			self.lock.release()


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
