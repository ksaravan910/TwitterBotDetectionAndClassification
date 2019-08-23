#!/usr/bin/env python
# coding: utf-8
# Honours Project 2019
# Krithika Saravanan, 100970975
# Run with Python 3.6
# Uncomment all method call lines

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from decimal import Decimal
import pprint
from botometer import Botometer
import tweepy
import json
import re
import preprocessor as p
import itertools
import pickle
from string import punctuation
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter


pp = pprint.PrettyPrinter(indent=4)

C_KEY = 'rdFeZ2ePyDf9qFhNGzkKGEC22'
C_SECRET = 'csvkpCZziAgbngIPjH9Gi8P2R3H1fNyQr3FpvsE3fh0jmXKI74'
A_TOKEN = '878335163121287169-sHzBMdW9I1HVlcWFWdvaj7wIMsKheZm'
A_TOKEN_SECRET = 'fgy1huoiJgA8fDSfpdz5rnNPvPbGtXvtiTL3RGPv5PtHm'
mashape_key = "e7b7a5ab38msh5ddc881afcc3bdcp101997jsn03924e682235"
twitter_app_auth = {
    'consumer_key': C_KEY,
    'consumer_secret': C_SECRET,
    'access_token': A_TOKEN,
    'access_token_secret': A_TOKEN_SECRET,
}

auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
botometer = Botometer(wait_on_ratelimit=True, mashape_key=mashape_key, **twitter_app_auth)

# User is exactly the user object from the request.
# Scores contains the overall classification results. 
# The english score uses all six categories of features
# The universal score omits sentiment and content features, both of which are English-specific.
# Categories gives subscores for each of the six feature classes.

# Content, sentiment = English specific features
# Language independent features = Friend, network, temporal, user

def get_bom_scores():
    accounts = []
    scores = {}
    # Read scores from file into list
    with open('accounts.txt', 'r') as fileobj:
        for row in fileobj:
            row = row.rstrip('\n')
            accounts.append(row)
    # Get botometer scores for a list of accounts
    for handle, result in botometer.check_accounts_in(accounts):
        try:
            tweet = api.user_timeline(screen_name=handle, count=1, include_rts=True)[0]
            # If user profile language is english print english score
            if (tweet.lang == 'en' or tweet.lang == 'und' and tweet.possibly_sensitive == False):
                english_score = result['scores']['english']
                scores[handle] = english_score
                print(handle + ' ' + str(english_score))
            else:
                print('account ' + handle + ' skipped')
        # No tweets to analyze; skip and go to next handle
        except:
            print('Error: account ' + handle + ' skipped')
            continue
    with open('scores.txt', 'w') as file:
        file.write(json.dumps(scores))
    return scores

scores = get_bom_scores()

def get_bot_handles():
    # Read scores from file
    scores = {}
    bots = []
    with open('scores.txt', 'r') as file_obj:
        data = file_obj.read().replace('{', '').replace('}', '').replace('\"', '').split(',')
        for line in data:
            handle, score = line.strip().split(':')
            scores[handle] = score.strip()
            if (Decimal(score) >= 0.43):
                bots.append(handle)
    outfile = open('bots.txt', 'w')
    for b in bots:
        # write line to output file
        outfile.write(b)
        outfile.write("\n")
    outfile.close()
    return bots

bots = get_bot_handles()

def get_bot_all_scores():
    accounts = []
    scores = {}
    # Read scores from file into list
    with open('bots.txt', 'r') as fileobj:
        for row in fileobj:
            row = row.rstrip('\n')
            accounts.append(row)
    # Get botometer scores for a list of accounts
    for handle, result in botometer.check_accounts_in(accounts):
        try:
            tweet = api.user_timeline(screen_name=handle, count=1, include_rts=True)[0]
            # If user profile language is english print english score
            if (tweet.lang == 'en' or tweet.lang == 'und' and tweet.possibly_sensitive == False):
                score = result
                scores[handle] = score
                print(handle + ' ' + str(score))
            else:
                print('account ' + handle + ' skipped')
        # No tweets to analyze; skip and go to next handle
        except:
            print('Error: account ' + handle + ' skipped')
            continue
    with open('scores.txt', 'w') as file:
        file.write(json.dumps(scores))
    return scores

scores = get_bot_all_scores()

# Gets a set number of tweets for a list of bots
def get_tweets():
    # Removes URLs, handles, reserved words from tweets
    p.set_options(p.OPT.URL, p.OPT.MENTION, p.OPT.RESERVED)
    # Stores tweets and handles
    tweets_map = {}
    bad_chars = list(punctuation)
    bad_chars.remove('!')
    bad_chars.remove('.')
    bad_chars.remove('?')
    bad_chars.append('–')
    bad_chars.append('...')
    bad_chars.append('..')
    bad_chars.append('')
    with open('bots.txt', 'r') as file_obj:
        for row in file_obj:
            handle = row.strip()
            try:
                tweets = api.user_timeline(screen_name=handle, count=100, tweet_mode='extended', include_rts=False)
                for tweet in tweets:
                    try:
                        if (tweet.lang == 'en' or tweet.lang == 'und' and tweet.possibly_sensitve == False):
                            words = tweet.full_text.split(' ')
                            new_words = []
                            for wrd in words:
                                # Remove words where letters and numbers are mixed like LX23: to do
                                # Remove monetary values $325 and numbers with decimals in the middle
                                # Replaces THIIIIIIIIS with THIS
                                wrd = re.sub(r'\d+', '', wrd)
                                wrd = re.sub(re.compile(r'(.)\1{2,}'), r'\1', wrd)
                                new_words.append(wrd)

                            words = new_words
                            cleaned_tweet = ' '.join(words)

                            # Using replace() to remove bad_chars
                            cleaned_tweet = p.clean(cleaned_tweet)
                            for char in bad_chars:
                                cleaned_tweet = cleaned_tweet.replace(char, '')

                            if (cleaned_tweet != ""):
                                # Appending tweets to the empty array tmp
                                tweets_map.setdefault(handle, []).append(cleaned_tweet)
                                # Remove duplicate tweets
                                tweets_set = set(tweets_map[handle])
                                # Convert back to original format
                                tweets_map[handle] = list(tweets_set)

                                print(handle + " " + cleaned_tweet)
                        else:
                            continue
                    except tweepy.TweepError:

                        continue
            except:
                continue

    return tweets_map

tweets_map = get_tweets()


# Removes bots that have less than 20 tweets in the dictionary
def clean_tweets_dict(this_map):
    for key in list(this_map):
        if (len(this_map[key]) < 50):
            this_map.pop(key)
    with open('tweets.pickle', 'wb') as f:
        pickle.dump(this_map, f)
    return this_map

this_map = clean_tweets_dict(tweets_map)


def sentiment_analysis(sentiment_values, num_tweets):
    tweet_count = 0
    print('SENTIMENT ANALYSIS: \t' + str(num_tweets) + ' tweets')
    # Load map from pickle file
    with open('tweets.pickle', 'rb') as f:
        result = pickle.load(f)

    print('num bots ' + str(len(result)))
    analyzer = SentimentIntensityAnalyzer()
    for key in result:
        print('num tweets ' + str(len(result[key])))
        tweet_count = tweet_count + len(result[key])
        user_sentiment = 0.0
        for tweet in itertools.islice(result[key], 0, num_tweets):

            vs = analyzer.polarity_scores(tweet)
            print('{:-<65} {}'.format(tweet, str(vs['compound'])))
            # Average scores over each user to find final score
            user_sentiment += vs['compound']
        avg_sentiment = round(user_sentiment / num_tweets, 4)
        print('AVERAGE SENTIMENT FOR USER: \t' + key + '\t\t' + str(avg_sentiment))
        # Add to map
        sentiment_values.setdefault(key, []).append(avg_sentiment)
    print('total tweets ' + str(tweet_count))
sentiment_values = {}
# Compute average sentiment over 20 tweets
sentiment_analysis(sentiment_values, 20)
# Compute average sentiment over 30 tweets
sentiment_analysis(sentiment_values, 30)
# Compute average sentiment over 40 tweets
sentiment_analysis(sentiment_values, 40)
# Compute average sentiment over 50 tweets
sentiment_analysis(sentiment_values, 50)

positive_bots = []
negative_bots = []
neutral_bots = []
def classify_bots(sentiment_values, pos):
    if (pos == 0):
        value = 20
    elif (pos == 1):
        value = 30
    elif (pos == 2):
        value = 40
    else:
        value = 50
    print('\nCLASSIFY: \t' + str(value) + ' tweets')

    for handle, sent_arr in sentiment_values.items():

        if (Decimal(sent_arr[pos]) >= 0.05):
            positive_bots.append(handle)
            print('positive' + handle)
        elif (Decimal(sent_arr[pos]) <= -0.05):
            negative_bots.append(handle)
            print('negative' + handle)
        else:
            print('neutral' + handle)
            neutral_bots.append(handle)

    print('POSITIVE BOTS: \t' + str(len(positive_bots)))
    print('NEGATIVE BOTS: \t' + str(len(negative_bots)))
    print('NEUTRAL BOTS: \t' + str(len(neutral_bots)))

# Classifies bots using the 1st value
classify_bots(sentiment_values, 0)
# Classifies bots using the 2nd value
classify_bots(sentiment_values, 1)
# Classifies bots using the 3rd value
classify_bots(sentiment_values, 2)
# Classifies bots using the 4th value
classify_bots(sentiment_values, 3)
