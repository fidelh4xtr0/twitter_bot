import tweepy
import selenium
import math
import requests
import os
import json
import time
import random
import datetime
import textwrap
from dateutil import parser



search_url = "https://api.twitter.com/2/tweets/search/recent"

bot_ids = ['1434306349417082884',
           '1428910863231168517',
           '1458651028476375047',
           '1489202597995200514', 
           '1490921395680854017']

quotes = []


global option
global reply
class Tweet:
    def __init__(self):
        self.max_length = 260
            
        # Credentials
        self.api_key = self.get_credentials()[0][1]
        self.api_secret = self.get_credentials()[1][1]
        self.bearer = self.get_credentials()[2][1]
        self.access_token = self.get_credentials()[3][1]
        self.access_token_secret = self.get_credentials()[4][1]
        

    #Authentication Functions


    def bearer_oauth(self,r):
        global option
        """
        Method required by bearer token authentication.çc
        """

        r.headers["Authorization"] = f"Bearer {self.bearer}"
        if option == 0:
            r.headers["User-Agent"] = "v2UserMentionsPython"
        elif option == 1:
            r.headers["User-Agent"] = "v2RecentSearchPython"
        elif option == 2:
            r.headers["User-Agent"] = "v2TweetLookupPython"
        elif option == 3:
           r.headers["User-Agent"] = "v2UserLookupPython"
        return r

    def get_credentials(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'creds')
        cred_file = open(filename,'r')
        creds = []
        for line in cred_file.readlines():
            creds.append(line.strip("\n").split("="))
            
        return creds[0],creds[1],creds[2],creds[3],creds[4],creds[5],creds[6]
        

    def create_url(self,check_type):
        if check_type == "mentions":
            user_id = self.get_credentials()[5][1]
            return "https://api.twitter.com/2/users/{}/mentions".format(user_id)

    #Tweet Preparation


    def connect_to_endpoint(self, url, params):
        response = requests.get(url, auth=self.bearer_oauth, params=params)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()
    
    def get_body(self):
        post = random.choice(quotes) + " #abolishNATO"
        self.prevent_repeat(post)
        return post

    def prepare_tweet(self):
        body = self.get_body()
        post = textwrap.wrap(body,width=self.max_length-1)
        return post
    
    def new_tweet(self,client,tweet_id):
        global option
        global reply
        option = 0
        post = self.prepare_tweet()
        posts = len(post)
        count=0
        for p in post:
            count+=1
            if posts > 1:
                tweet = f'{p} {count}/{posts}'
            else:
                tweet = p
            print(tweet, len(tweet))
            if post.index(p) == 0:
                if reply:
                    try:
                        client.create_tweet(text=tweet,in_reply_to_tweet_id=tweet_id)
                    except Forbidden:
                        time.sleep(10)
                        client.create_tweet(text=tweet,in_reply_to_tweet_id=tweet_id)
                else:
                    try:
                        client.create_tweet(text=tweet)
                        continue
                    except:    
                        time.sleep(10)
                        client.create_tweet(text=tweet)
                        continue
            elif post.index(p) < len(p):
                time.sleep(20)
                tweet_text = post[post.index(p)-1]
                if '"' in tweet_text:
                    if tweet_text.startswith('"'):
                        tweet_text=tweet_text.split('"')[1]
                    else:
                        tweet_text=tweet_text.split('"')[0]
                query_params = {'query': f'from:{self.get_credentials()[6][1]}"{tweet_text}"','tweet.fields': 'author_id'}
                tweet_id = self.get_tweet_id(query_params)
                try:
                    client.create_tweet(text=tweet,in_reply_to_tweet_id=tweet_id)
                except:
                    time.sleep(10)
                    client.create_tweet(text=tweet,in_reply_to_tweet_id=tweet_id)
    
    
    def get_tweet_id(self, query):
        json_response = self.connect_to_endpoint(search_url, query)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        return json_object

    def debug(self,json_object):
        for entry in json_object['data']:
            if entry['author_id'] not in bot_ids:
                print(entry['author_id'], entry['text'])
        
        exit(0)
        

                
    def check_mentions(self, client):
        global reply
        global option
        option = 1
        pull_type = "mentions"
        url = self.create_url(pull_type)
        params = self.get_params()
        json_response = self.connect_to_endpoint(url, params)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        for response in json_object["data"]:
            reply = True
            date_posted = parser.isoparse(response['created_at'])
            now = datetime.datetime.now(datetime.timezone.utc)
            now = now.replace(tzinfo=None)
            date_posted = datetime.datetime(date_posted.year,date_posted.month,date_posted.day,date_posted.hour,date_posted.minute,date_posted.second)        
            time_diff = now - date_posted
            minute_diff = time_diff.total_seconds()/60

            if  minute_diff <= 5 and response['author_id'] not in bot_ids:   
                self.new_tweet(client,response['id'])
        

    def get_params(self):
        # Tweet fields are adjustable.
        # Options include:
        # attachments, author_id, context_annotations,
        # conversation_id, created_at, entities, geo, id,
        # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
        # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
        # source, text, and withheld
        return {"tweet.fields": "created_at,author_id"}
            
    def prevent_repeat(self, quote):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'used')
        used = open(filename,'r+')
        if quote in used.read():
            quote = self.prepare_tweet()
        used.seek(0, os.SEEK_END)
        used.write(f'^{quote}\n')
        used.seek(0, os.SEEK_SET)
        used_raw = used.read()
        total_quotes = used_raw.split('^')
        if len(total_quotes) > 15:
            used.truncate(0)
        used.close()    
        
    
def main():
    global reply
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'quotes.txt')
    text = open(filename,'r')
    
    txt = text.read()
    for quote in txt.split('^'):
        if len(quote)<3:
            continue
        else:
            quotes.append(quote)
        
    tweet = Tweet()

    client = tweepy.Client(
        consumer_key= tweet.api_key,
        consumer_secret=tweet.api_secret,
        access_token=tweet.access_token,
        access_token_secret=tweet.access_token_secret
    )                
    reply = False
    date = datetime.datetime.now()


    if date.minute ==0:
        tweet.new_tweet(client,0)
    else:
        print("Let's go check those mentions")
        tweet.check_mentions(client)


if __name__ == "__main__":
    main()
