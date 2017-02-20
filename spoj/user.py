import requests
import json
from bs4 import BeautifulSoup
from collections import OrderedDict

SPOJ_URL = 'https://www.spoj.com/users/'

def getUserData(handle):

	attributes = OrderedDict()

	#
	#	Fetching the page.
	#
	r = requests.get(SPOJ_URL + handle).text.encode('utf-8')
	soup = BeautifulSoup(r, "html.parser")
	mydiv = soup.findAll('table', { 'class' : 'table table-condensed' })
	
	#
	#	if mydiv is empty, that means the user has not solved any problems
	#	or the user doesn't exist.
	#
	if not mydiv:
		return None

	result = [td.text for tr in mydiv[0].findAll('tr') for td in tr.findAll('td') if td.text != '']
	
	attributes['handle'] = handle
	attributes['solved'] = result
	return attributes	

if __name__ == '__main__':
	a = getUserData('shikhar_gupta_')
	print(json.dumps(a, indent=4))
