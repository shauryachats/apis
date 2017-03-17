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

def clean(string):
    return string.encode('ascii','ignore').decode('UTF-8')


# TODO : Try to parse the SVG image of the rating curve, to extract all data about the contest rating at any time.
# REFACTOR : Split all the parsing methods into seperate, for easy debugging.

def getUserData(handle):

    # Dictionary returning all the scraped data from the HTML.    
    attributes = OrderedDict()

    soup = downloadUserPage(handle)

    # The profile_tab contains all the data about the user.
    profileTab = soup.find('div', {'class': 'user-profile-container'})
    #print(profileTab)

    attributes['real_name'] = profileTab.find('header').h2.text
    attributes['handle'] = handle
    attributes['display_picture'] = profileTab.find('header').img['src']

    #   If there is no display_picture, convert the relative link into an absolute link.
    if (attributes['display_picture'].startswith('/sites/')):
        attributes['display_picture'] = "https://www.codechef.com/" + attributes['display_picture']    

    handleDetails = profileTab.find('ul', {'class' : 'side-nav'})

    for detail in handleDetails.findAll('li'):
        parseText = detail.text.replace('\n','')

        if parseText.startswith('Username'):
            attributes['stars'] = parseText.split('★')[0][-1]
        else:
            parseText = parseText.split(':')
            attributes[convertToKey(parseText[0])] = parseText[1].encode('ascii','ignore').decode('UTF-8') 

    #
    #   Removing unwanted keys from attributes (for now)
    #
    unwantedKeys = ["studentprofessional", "teams_list", "link", "motto"]
    attributes = removeKeys(attributes, unwantedKeys)

    #
    #   Parsing fully solved and partially solved problems from the page.
    #
    problemSolved = profileTab.find('section', {'class' : 'rating-data-section problems-solved'})
    problemSolved = problemSolved.find('div', {'class' : 'content'})

    fullySolved = problemSolved.findAll('article')[0]
    partiallySolved = problemSolved.findAll('article')[1]

    attributes['fully_solved'] = {}
    attributes['partially_solved'] = {}

    for contest in fullySolved.findAll('p'):
        contest = clean(contest.text).split(':')
        attributes['fully_solved'][contest[0]] = contest[1].split(',')

    for contest in partiallySolved.findAll('p'):
        contest = clean(contest.text).split(':')
        attributes['partially_solved'][contest[0]] = contest[1].split(',')

    # Rating table

#    attributes['rating'] = {}
#    attributes['rating']['overall'] = int(soup.find('div', {'class' : 'rating-number'}).text)
#    attributes['rating']['max'] = soup.find('div', {'class' : 'rating-star'}).findNext('small').text

    print(attributes['rating'])

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
    getUserData('shauryachats')
    #print(json.dumps(getUserData('shauryachats'), indent=4))