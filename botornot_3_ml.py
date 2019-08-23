#!/usr/bin/env python
# coding: utf-8
# Honours Project 2019
# Krithika Saravanan, 100970975
# Run with Python 3.6
# credit to https://towardsdatascience.com/creating-the-twitter-sentiment-analysis-program-in-python-with-naive-bayes-classification-672e5589a7ed
# for ml model implementation
from decimal import Decimal
import pprint
import tweepy
import itertools
import pickle
import csv
import nltk
import os
import re
from nltk.tokenize import word_tokenize
from string import punctuation
from nltk.corpus import stopwords

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

def build_train_set(corpus_file):
    training_dataset = []
    with open(corpus_file, encoding='utf-8') as csvfile:
        line_reader = csv.reader(csvfile, delimiter=',')
        for row in line_reader:
            training_dataset.append({'tweet_id': row[0], 'label': row[1], 'topic': row[2], 'text': row[3]})
    return training_dataset

def build_test_set(num_tweets):
    test_set = []
    with open('tweets.pickle', 'rb') as f:
        result = pickle.load(f)
    for key in result:
        user_sentiment = 0.0
        for tweet in itertools.islice(result[key], 0, num_tweets):
            tweet_dict = dict()
            tweet_dict['text'] = tweet
            tweet_dict['label'] = None
            tweet_dict['handle'] = key
            test_set.append(tweet_dict)
            if 'tweet_id' in tweet:
                print('tweet id')
                test_set.remove(tweet)
    return test_set

test_data_set = build_test_set(50)

class PreProcessTweets:
    def __init__(self):
        self._stopwords = set(stopwords.words('english') + list(punctuation) + ['AT_USER', 'URL'])

    def process_tweets(self, list_of_tweets):
        processed_tweets = []

        for tweet in list_of_tweets:
                processed_tweets.append((self._process_tweet(tweet["text"]), tweet["label"]))
        return processed_tweets

    def _process_tweet(self, tweet):
        tweet = tweet.lower()  # convert text to lower-case
        tweet = re.sub(' \d+', '', tweet)
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet)  # remove URLs
        tweet = re.sub('@[^\s]+', 'AT_USER', tweet)  # remove usernames
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet)  # remove the # in #hashtag
        tweet = word_tokenize(tweet)  # remove repeated characters (helloooooooo into hello)
        return [word for word in tweet if word not in self._stopwords]

def build_vocabulary(preprocessed_training_data):
    print('build vocab')
    all_words = []
    for (words, sentiment) in preprocessed_training_data:
        all_words.extend(words)
    wordlist = nltk.FreqDist(all_words)
    word_feat = wordlist.keys()
    return word_feat

def extract_features(tweet):
    tweet_words = set(tweet)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in tweet_words)
    return features

def save_classifier(classifier):
    print('save classifier')
    file = open('sentiment_classifier.pickle', 'wb')
    pickle.dump(classifier, file, -1)
    file.close()

def load_classifier():
    print('load classifier')
    file = open('sentiment_classifier.pickle', 'rb')
    classifier = pickle.load(file)
    file.close()
    return classifier

tweetProcessor = PreProcessTweets()
preprocessedTestSet = tweetProcessor.process_tweets(test_data_set)
training_data = build_train_set('training_data.csv')
preprocessedTrainingSet = tweetProcessor.process_tweets(training_data)
word_features = build_vocabulary(preprocessedTrainingSet)

myTestSet = ['Suicide Bomber Kills Officials in Mayor’s Office in Somalia’s CapitalSuicide Bomber Kills Officials in Mayor’s Office in Somalia’s Capital',
            'Trump Says Mueller Was ‘Horrible’ and Republicans ‘Had a Good Day’',
            'DO This gives a very good view of the water. Small excursions to close by islands might be possible.',
            'please eat something healthy',
            'You have a great sense of humor.',
            'Germany In Political Turmoil As Coalition Talks Fail lmao',
            'Confidence goes a long way. Even if it doesn’t come naturally  fake it ’til you make it!',
            'MIDRANGE Try it good place hangout in eveinings and night. Chinese and Malaysian food.',
            'As Trump Accuses Iran He Has One Problem His Own Credibility',
            'please dont forget to listen to a song you enjoy']

if os.path.isfile('sentiment_classifier.pickle'):
    print('pickle file exists')
    cl = load_classifier()
    for tweet in myTestSet:
        print(tweet)

    NBResultLabels = [cl.classify(extract_features(tweet)) for tweet in myTestSet]
    testFeatures = nltk.classify.apply_features(extract_features, preprocessedTestSet[0:100])
    print(nltk.classify.accuracy(cl, testFeatures))
    cl.show_most_informative_features(5)
    print('classification done')
else:
    print('pickle file doesnt exist')
    trainingFeatures = nltk.classify.apply_features(extract_features, preprocessedTrainingSet)
    NBayesClassifier = nltk.NaiveBayesClassifier.train(trainingFeatures)
    save_classifier(NBayesClassifier)
    NBResultLabels = [NBayesClassifier.classify(extract_features(tweet)) for tweet in myTestSet]


