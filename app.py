import tweepy
import sys
import os
import time
import flask
import json
import requests
import urllib2
import random

#stores the ids for the tweets and images used
usedTweets = []
usedPictures = []

#class definitions
#########################################################################
class tweetInfo:
    def __init__(self, tweet, author, picture, tweetID, authorID):
        self.tweet =  tweet
        self.author = author 
        self.authorPic = picture
        self.tweetID = tweetID
        self.tweetLink = "https://twitter.com/statuses/"+str(tweetID)
        self.authorLink = "https://twitter.com/intent/user?user_id="+str(authorID)
        
    def setBgImg(self, bgImgID):
        self.bgImage = "http://media.gettyimages.com/photos/-id"+str(bgImgID)

class apiKeys:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, getty_api_key):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret 
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.getty_api_key = getty_api_key

#checks that the url for the image is valid
#returns boolean
##########################################################################
def checkURL(idNum):
    valid = False
    gettyURL = "http://media.gettyimages.com/photos/-id"
    #gets twitter handle
    request = requests.get(gettyURL+idNum)
    
    #checks to see if the user exists
    if(request.status_code != 200):
        valid = False
    else:
        valid = True
    
    return valid

#gets tweet and stores it into an object
#returns a boolean and tweetInfo object
##########################################################################
def getTweet(searchTerm, keys):
    
    #twitter API key setup
    auth = tweepy.OAuthHandler(keys.consumer_key , keys.consumer_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    
    api = tweepy.API(auth)
    tweets = []
    
    #searches for tweets
    for tweet in tweepy.Cursor(api.search, q=searchTerm, lang="en").items(7):
        if (not tweet.retweeted) and ('RT @' not in tweet.text):
            tweets.append(tweetInfo(tweet.text, tweet.author.name, tweet.author.profile_image_url_https, tweet.id, tweet.author.id))
    
    
    #chooses an object from the list at random
    if(len(tweets) > 0):
        return True, random.choice(tweets)
    else:
        return False, tweetInfo("", "", "", "", "")
    
##############################################################################

#gets image id from getty
#returns 
def getImage(searchTerm, keys):
    ########## GETTY API #####################################################
    #gets the id's from the search
    url_test = 'https://api.gettyimages.com/v3/search/images?fields=id,title,thumb,referral_destinations&sort_order=best&phrase='+searchTerm
    headers = {'Api-Key' : keys.getty_api_key}
    res = requests.get(url_test, headers=headers, )
    data  = res.json()
    
    IDs = []
    anID = ""
    
    #gets all IDs from json, caps at 20
    count = 0
    for element in data['images']:
        if(count >= 20):
            break
        
        anID = element['id']
        IDs.append(anID)
        
        count += 1
    
    #make sure that the image id link works properly
    success = False;
    for i in range(0,len(IDs)):
        anID = random.choice(IDs)
        if(checkURL(anID) == True):
            success = True
            break
        
    return success, anID

#launches Flask
##########################################################################
app = flask.Flask(__name__)

@app.route('/')
def index(aTweet = None, url = None, anAuthor = None, authorPic = None, tweetLink = None, authorLink = None):
    
    #set all api keys onto the object
    keys = apiKeys(os.getenv("TWITTER_CONSUMER_KEY") ,
                        os.getenv("TWITTER_CONSUMER_SECRET"),
                        os.getenv("TWITTER_ACCESS_TOKEN"), 
                        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
                        os.getenv("GETTY_API_KEY"))
    
    #after 10 page reloads, it resets the lists that keep track of the 
    #IDs used
    print "LENGTH OF LIST: "+str(len(usedTweets))
    if(len(usedTweets) >= 10):
        print "RESET"
        del usedTweets[:]
        del usedPictures[:]
    
    #gets random search term
    termList = ["potatoes", "potato", "sweet potato", "yams", "yam", "radishes",
                "onions", "ginger", "beets", "garlic", "celery", "jicama"]
    searchTerm = random.choice(termList)
    
    #gets the proper information from th etweet and the getty images
    success = False
    while(success == False):
        searchTerm = random.choice(termList)
        
        #get tweetInfo object and boolean
        success, chosenTweet = getTweet(searchTerm, keys)
        
        #makes sure that there is a tweet to use
        if(success == False):
            continue
        
        #get image ID and boolean
        success, anID = getImage(searchTerm,
                        keys)
        
        #checks agains the used IDs
        if chosenTweet.tweetID in usedTweets:
            success = False
            print str(chosenTweet.tweetID), "already used"
            
        if anID in usedPictures:
            success = False
            print str(anID), "already used"
        
        #if the values have not been used, then add them to the list of used
        #items
        if(success == True):
            usedTweets.append(chosenTweet.tweetID)
            usedPictures.append(anID)
            
            #set background image based on the image id
            chosenTweet.setBgImg(anID)
    
    #print usedTweets
    #print usedPictures
    
    return flask.render_template("index.html", 
        aTweet = chosenTweet.tweet, 
        url= chosenTweet.bgImage, 
        anAuthor = chosenTweet.author, 
        authorPic = chosenTweet.authorPic,
        tweetLink = chosenTweet.tweetLink,
        authorLink = chosenTweet.authorLink)

app.run(
        host=os.getenv('IP', '0.0.0.0'),
        port=int(os.getenv('PORT', 8080))
)
##########################################################################