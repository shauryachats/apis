"""
   Codechef Unofficial API.

   Parses all the user data in JSON.

   Author: Shaurya Chaturvedi
           shauryachats@gmail.com

"""

from bs4 import BeautifulSoup
import requests
import os
from collections import OrderedDict
import json
import logging
import re
import datetime
import time



""" 
    downloadUserPage() returns the BeautifulSoup object of the handle, if found.
    If not, it raises an Exception.
"""
def downloadUserPage(handle):

    URL = "https://www.codechef.com/users/" + handle
    web_page = None

    try:
        web_page = requests.get(URL,headers={'User-Agent': 'Mozilla/5.0'})
    except IOError:
        raise IOError('Cannot connect to codechef.com')

    #
    #   Apparently, if the handle is not present, a 302 response is returned.
    #
    for response in web_page.history:
        if response.status_code == 302:
            raise Exception('User not found.')

    return BeautifulSoup(web_page.text.encode('utf-8').strip(), "html.parser")

#
#   Converts To ken into to_ken
#
def convertToKey(token):
    temp = token.lower().replace(' ', '_')
    return ''.join(ch for ch in temp if ch.isalnum() or ch == '_')

#
#   Utility to remove a list of keys from a dictionary.
#
def removeKeys(attr, keyList):
    
    for key in keyList:
        try:
            attr.pop(key, None)
        except KeyError:
            pass

    return attr

#
#   Helper function for getUserData() to parse the list of complete and partial problems.
#
def parseProblems(problemsC):
    problemDict = OrderedDict()

    for problemGroup in problemsC:
        problemList = []
        problemGroupList = problemGroup.findAll('a')
        for problem in problemGroupList:
            problemList.append(problem.text)
        
        #Added arbitary contest code "PRACTICE" for practice problems.
        problemDict[ "PRACTICE" if problemGroup.b.text.startswith("Practice") else problemGroup.b.text ] = problemList

    return problemDict

"""
    getUserData() does all the dirty work of parsing the HTML and junxing it altogether
    in a crude 'attributes' dict.
"""

# TODO : Try to parse the SVG image of the rating curve, to extract all data about the contest rating at any time.
# REFACTOR : Split all the parsing methods into seperate, for easy debugging.

def getUserData(handle):

    # Dictionary returning all the scraped data from the HTML.    
    attributes = OrderedDict()

   # print("Yay")
    soup = downloadUserPage(handle)
    #print(soup)

    # The profile_tab contains all the data about the user.
    profileTab = soup.find('div', {'class': 'profile'})

    #   This profile consists of four tables.
    #
    #   ->  The first table just contains the real name of the user, and the display picture.
    #   ->  The second table contains the info about the user, and the problems info.
    #   ->  The third table contains the problem statistics.
    #   ->  The fourth table contains the performance graphs, in SVG format.
    #

    #Add the handle too, for convinenece.
    attributes['handle'] = handle

    #The real name is present in a simple div.user-name-box,
    attributes['realname'] = profileTab.find('div', {'class' : 'user-name-box'}).text

    #The displayPicture link is present in div.user-thumb-pic
    attributes['display_picture'] = profileTab.find('div', {'class' : 'user-thumb-pic'}).img['src']

    if (attributes['display_picture'].startswith('/sites/')):
        attributes['display_picture'] = "https://www.codechef.com/" + attributes['display_picture']    

    row = profileTab.table.findNext("table").tr

    #
    #   Parsing the personal data of the user.
    #
    while not row.text[1:].startswith("Problems"):

        # Strip the text of unwanted &nbsp, and splitting via the :\
        parsedText = row.text.replace("\n", '').split(':')

        attributes[ convertToKey(parsedText[0]) ] = parsedText[1]
        row = row.findNext("tr")

    #
    #   Removing unwanted keys from attributes (for now)
    #
    unwantedKeys = ["studentprofessional", "teams_list", "link", "motto"]
    attributes = removeKeys(attributes, unwantedKeys)

    #
    #   Parsing the complete problem list.
    #
    problemsComplete = row.td.findNext('td').findAll('p')
    completeProblemDict = OrderedDict()
    attributes['solved'] = parseProblems(problemsComplete)

    #
    #   Parsing the partial problem list.
    #
    problemsPartial = row.findNext('tr').td.findNext('td').findAll('p')
    partialProblemDict = OrderedDict()
    attributes['partial'] = parseProblems(problemsPartial)

    #
    #   Parsing the problem_stats table to get the number of submissions, WA, RTE, and the stuff.
    #
    problemStats = soup.find("table", id="problem_stats").tr.findNext('tr').findAll('td')
    problemStats = [item.text for item in problemStats]


    #
    #   Parsing the problem submission statistics.
    #
    stats = {}
    keys = ['pc', 'pp', 'ps', 'acp', 'acc', 'wa', 'cte', 'rte', 'tle']
    for i in range(0, len(problemStats)):
        stats[keys[i]] = int(problemStats[i])
    attributes['stats'] = stats

    #
    #   Parsing the rating table to get the current ratings of the user.
    #
    ratingTable = soup.find("table", {'class': "rating-table"}).findAll('tr')[1:4]
    ratingList = {}
    keys = ['long', 'short', 'ltime']
    for i, tr in enumerate(ratingTable):
        tr = tr.findAll('td')[1:3]
        parsedText = tr[0].text
        # If the user has not yet got a rank, set it to 0.
        if (parsedText == "NA"):
            parsedText = "0/0"
        parsedText = parsedText.split('/')
        ratingList[ keys[i] ] = [   int(parsedText[0]), 
                                    int(parsedText[1]), 
                                    float(tr[1].text.strip('(?)')) 
                                ] 

    attributes['rating'] = ratingList 
    return attributes

#
#   Returns the most recent submittions by a user.
#
def getRecent(handle, numberOfSub = 10):

    logging.debug("In getRecent(" + handle + ')')
    content = [] 
    pageno = 0

    while (len(content) < numberOfSub):
        soup = downloadRecentPage(handle, pageno)

        for tr in soup.table.tbody.findAll('tr'):
            tds = tr.findAll('td')
            data = {}

            #TODO: Try to reduce timestamp conversion module.
            subTime = tds[0].text
            #Try to parse it as a strptime object.
            try:
                a = datetime.datetime.strptime(subTime, "%I:%M %p %d/%m/%y")
                subTime = int(time.mktime(a.timetuple()))
            except ValueError:
                #This was submitted less than 24 hours ago.
                texts = subTime.split(' ')
                val = int(texts[0]) #Get the numeric part.
                if texts[1] == 'min':
                    val *= 60
                elif texts[1] == 'hours':
                    val *= 3600
                else:
                    pass
                subTime = int(time.mktime((datetime.datetime.now().timetuple()))) - val
            
            data['sub_time'] = subTime
            data['problem_code'] = tds[1].a['href'].split('/')[-1]
            data['type'] = tds[2].span['title']
            data['points'] = tds[2].text
            if data['points'] != '':
                data['type'] = 'accepted'
            data['language'] = tds[3].text

            content.append( data )

        pageno += 1

    #Truncating0
    logging.debug("getUserData = " + json.dumps(content[:numberOfSub], indent = 4))
    return content[:numberOfSub]

if __name__ == '__main__':
    print(json.dumps(getUserData('shauryachats'), indent=4))