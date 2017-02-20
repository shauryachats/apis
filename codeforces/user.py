'''
	Codeforces Helper API.

	Extracts raw data from the official CF API
	to present some more facts, easily.

'''

import requests
import json
from collections import OrderedDict

CF_SUBMISSION_URL = 'http://codeforces.com/api/user.status?handle='
CF_INFO_URL = 'http://codeforces.com/api/user.info?handles='

def getUserData(handle):

	attributes = OrderedDict()

	#
	#	Getting user info.
	#
	r = requests.get(CF_INFO_URL + handle).text
	cfdata = json.loads(r)

	# Rogue request deserves an empty JSON.
	if cfdata['status'] == 'FAILED':
		return '{}'

	for key in ['rating', 'country', 'maxRating', 'handle', 'organization', 'contribution', 'rank']:
		#If key isn't present, ignore.
		try:
			attributes[key] = cfdata['result'][0][key]
		except Exception as e:
			pass
	#
	#	Getting submission info.
	#
	r = requests.get(CF_SUBMISSION_URL + handle + '&from=1&count=100000').text
	cfdata = json.loads(r)

	solved_problems = set()

	for submission in cfdata['result']:
		if submission['verdict'] == 'OK':
			problemcode = str(submission['problem']['contestId']) + submission['problem']['index']
			solved_problems.add(problemcode)

	attributes['solved'] = list(solved_problems)
	return json.dumps(attributes, indent=4)

if __name__ == '__main__':
	print(getUserData('anta'))