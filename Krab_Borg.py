#Krab_Borg allows users of SpongeBob subreddits to search the wiki
#The wiki is located at http://spongebob.wikia.com
#Created by claycot
#License: MIT License

#Import necessary libraries for web scraping
from bs4 import BeautifulSoup
from urllib.parse import urlparse

#Import necessary libraries for web requests
import praw
import time
import re
import requests
import bs4

#Import necessary libraries for string matching
from fuzzywuzzy import fuzz

#Import necessary libraries for filepath manipulation
import os

#Which reddit sub to run on
runOnSub = 'GASP_test'

#File path for episode list and episode links
botDir = os.path.dirname(os.path.abspath(__file__))
listPath = os.path.join(botDir, 'episodeList.txt')
linkPath = os.path.join(botDir, 'episodeLinks.txt')
logPath = os.path.join(botDir, 'replyLog.txt')

#Function to authenticate reddit account (allow bot to post)
def authenticateAccount():
    print('Authenticating reddit account...\n')
    #Create an instance of reddit through PRAW
    reddit = praw.Reddit('Krab_Borg', user_agent = 'web:Krab_Borg:v1.0')
    print('Authenticated reddit account as {}\n'.format(reddit.user.me()))
    return reddit

#Function to scrape the SpongeBob Wiki
def scrapeSite(url):
    scrape = requests.get(url)
    soup = BeautifulSoup(scrape.content, 'html5lib')
    return soup

#Function to scrape user comments
def scrapeComments(comLimit, reddit):
    print('Scraping reddit comments...\n')
    comNum = 1
    for comment in reddit.subreddit(runOnSub).comments(limit = comLimit):
        #print(comment.body)
        match = re.search('(?<=!episode ).*?(?=\n|$)', comment.body)
        #print(match)
        if match:
            if not comment.saved:
                print('Episode found in comment ID: ' + comment.id + '\n')
                #print(match.group(0)+ '\n\n')
                #print(match.group(0))
                matchedIndex = matchEpisode(match.group(0))
                writeResponse(matchedIndex, comment)
                comment.save()
    return 'Null'

#Function to update episode list
def updateList():
    listURL = 'http://spongebob.wikia.com/wiki/List_of_episodes_(simple)'
    websiteContents = scrapeSite(listURL)
    fileList = open(listPath, 'w', encoding = 'utf-8')
    fileLinks = open(linkPath, 'w', encoding = 'utf-8')
    for episode in websiteContents.select('tr td a'):
        if not (episode.has_attr('class')):
            if not (episode.get('title').startswith("Timeline")):
                fileList.write(episode.get_text() + '\n')
                fileLinks.write(episode.get('href') + '\n')
    fileList.close()
    print('Episode list updated successfully!\n')
    fileLinks.close()
    print('Episode links updated successfully!\n')    
    return

#Function to match comment to episode title
def matchEpisode(userString):
    highScore = 1
    matchIndex = -1
    lineIndex = 0
    with open(listPath, 'r', encoding = 'utf-8') as fileList:
        for episode in fileList:
            lineScore = fuzz.WRatio(userString, episode)
            if lineScore > highScore:
                #Debug lines for scoring algorithm
                #print(episode + ' ')
                #print(str(lineScore) + '\n')
                highScore = lineScore
                matchIndex = lineIndex
            lineIndex += 1
    print("Match found with a score of " + str(highScore) + '\n')
    return matchIndex

#Function to get an episode link
def getLink(episodeIndex):
    lineIndex = 0
    with open(linkPath, 'r', encoding = 'utf-8') as fileLinks:
        for episodeLink in fileLinks:
            if (lineIndex == episodeIndex):
                #print('http://spongebob.wikia.com' + episodeLink + '\n')
                return 'http://spongebob.wikia.com' + episodeLink.rstrip('\n')
            else:
                lineIndex += 1
                if (lineIndex > 9000):
                    print('Error: link not returned!\n')
                    return 'Error: link not returned'

#Function to get episode info
def getEpisodeInfo(episodeLink):
    target = 'Unassigned; error'
    website = scrapeSite(episodeLink)
    for item in website.select('h3 > span'):
        if item.get_text() == 'Characters':
            for sibling in item.parent.previous_siblings:
                if (sibling.name == 'p'):
                    target = sibling.get_text()
                    #print(target)
                    return target
    print('Error: episode summary not found on wiki!\n')
    return 'Error: episode summary not found on wiki!'    

#Function to write a response comment
def writeResponse(episodeIndex, comment):
    print('Getting episode summary from Spongebob Wiki...\n')
    #Reusable header and footer for reddit posts
    header = '**Krab_Borg searched SpongeBob Wiki and found the following:**\n\n'
    footer = '\n\nKrab_Borg is an automated bot.'
    if episodeIndex == -1:
        summary = '404: No Matching Episode!\n'
    else:
        epLink = getLink(episodeIndex)
        #print(epLink)
        summary = getEpisodeInfo(epLink) + \
              'For more information, visit the [Spongebob Wiki](' + \
              epLink + ')'
    print('Posting reddit comment!\n')
    redditComment = header + summary + footer
    print(redditComment)
    comment.reply(redditComment)
    print('Done posting comment!\n')
    return

#Function to run the Krab_Borg
def runKrabBorg(reddit):
    scrapeComments(250, reddit)
##    userRequest = scrapeComments(250, reddit)
##    if userRequest != 'Null':
##        matchedIndex = matchEpisode(userRequest)
##        writeResponse(matchedIndex, comment)
##    return

#Main function
def main():
    reddit = authenticateAccount()
    updateList()
    while True:
        runKrabBorg(reddit)
        print('Waiting for 60 seconds...\n')
        time.sleep(60)

#Main helper
if __name__ == '__main__':
    main()
