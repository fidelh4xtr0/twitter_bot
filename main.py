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

quotes = []


global option
global reply
class Tweet:
    def __init__(self):
        self.max_length = 280
            
        # Credentials
        self.api_key = self.get_credentials()[0][1]
        self.api_secret = self.get_credentials()[1][1]
        self.bearer = self.get_credentials()[2][1]
        self.access_token = self.get_credentials()[3][1]
        self.access_token_secret = self.get_credentials()[4][1]
        

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields

    def get_credentials(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'creds')
        cred_file = open(filename,'r')
        creds = []
        for line in cred_file.readlines():
            creds.append(line.strip("\n").split("="))
            
        return creds[0],creds[1],creds[2],creds[3],creds[4]
        

    def create_url(self,check_type):
    # Replace with user ID below
        if check_type == "mentions":
            user_id = 1490921395680854017
            return "https://api.twitter.com/2/users/{}/mentions".format(user_id)
        elif check_type == "anti-authoritarians":
            return "https://api.twitter.com/2/tweets/search/recent"


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

    def connect_to_endpoint(self, url, params):
        response = requests.get(url, auth=self.bearer_oauth, params=params)
        #print(response.status_code)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()
    
    def get_body(self):
        post = random.choice(quotes)

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
        for p in post:
            print(p)
            if post.index(p) == 0:
                if reply:
                    client.create_tweet(text=p,in_reply_to_tweet_id=tweet_id)
                    continue
                else:
                    client.create_tweet(text=p)
                    continue
            elif post.index(p) < len(p):
                time.sleep(20)
                tweet_text = post[post.index(p)-1]
                query_params = {'query': f'from:reds_bot"{tweet_text}"','tweet.fields': 'author_id'}
                tweet_id = self.get_tweet_id(query_params)["data"][0]["id"]
                client.create_tweet(text=p,in_reply_to_tweet_id=tweet_id)
    
    
    def get_tweet_id(self, query):
        json_response = self.connect_to_endpoint(search_url, query)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        return json_object

        

                
    def check_mentions(self, client):
        global reply
        global option
       # print(client.get_users_mentions(id="1489202597995200514"))
        option = 1
        pull_type = "mentions"
        url = self.create_url(pull_type)
        params = self.get_params()
        json_response = self.connect_to_endpoint(url, params)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        responses = len(json_object["data"])
        #date_posted = json_object["data"]
        #print(date_posted)
        for response in json_object["data"]:
            reply = True
            date_posted = parser.isoparse(response['created_at'])
            now = datetime.datetime.now(datetime.timezone.utc)
            now = now.replace(tzinfo=None)
            date_posted = datetime.datetime(date_posted.year,date_posted.month,date_posted.day,date_posted.hour,date_posted.minute,date_posted.second)
        
            #print (now,date_posted)
        
            time_diff = now - date_posted
            minute_diff = time_diff.total_seconds()/60

            
            print(minute_diff)
            if  minute_diff <= 5:            
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
    
    
    def is_anarchist(self,entry):
        global option
        option = 3
        #print(entry['author_id'])
        url = "https://api.twitter.com/2/users"
        params = {"user.fields":"description", "ids":entry["author_id"]}
        json_response = self.connect_to_endpoint(url, params)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        description = json_object["data"][0]['description'].lower()
        if ("anti-authoritarian" in description or
            "antiauthoritarian" in description or
            "anarchist" in description or
            "freedom" in description or
            "libertarian socialist" in description):
            return True
        
            
    def get_anti_authoritarians(self, client):
        global reply
        global option
        
        reply = True
        option = 2
        pull_type = "anti-authoritarians"
        url = self.create_url(pull_type)
        params = self.get_params()
        query_params = {'query': '(authoritarian OR dictator) (Stalin OR Mao OR Lenin OR Xi OR China OR Soviet OR CCP) -is:retweet','tweet.fields': 'author_id','max_results':"50"}
        #tweet_id = self.get_tweet_id(query_params)
        json_response = self.connect_to_endpoint(url, query_params)
        json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        count = 1
        for entry in json_object["data"]:
            #print(f"{entry['id']}: {entry['text']}")
            if self.is_anarchist(entry):
                print("We got a live one")
                client.create_tweet(text="Anti-authoritarian detected: @OnAuthorityBot you know what to do",in_reply_to_tweet_id=entry['id'])        
            count+=1
        #url = self.create_url(pull_type)
        #json_response = self.connect_to_endpoint(url, params)
        #json_object = json.loads(json.dumps(json_response, indent=4, sort_keys=True))
        #print(json_object)
        
    
def main():
    global reply
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'quotes.txt')
    text = open(filename,'r')
    
    txt = text.read()
    count=0
    for quote in txt.split('"'):
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
   # tweet.new_tweet(client)
    date = datetime.datetime.now()
    


    if date.minute == 0:
        tweet.new_tweet(client,0)
    elif date.hour == 12 and date.minute==0:
       # tweet.get_anti_authoritarians(client)
       exit(0)
    else:
        print("Let's go check those mentions")
        tweet.check_mentions(client)
    


if __name__ == "__main__":
    main()