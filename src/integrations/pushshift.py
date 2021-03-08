import json
import requests
from datetime import datetime


PUSHSHIFT_URL = "https://api.pushshift.io/reddit/search/submission/"


def get_ids_from_submissions_with_keywords_for_interval(subreddit, interval, keyword = None, size = 500):
    """Search for a keyword, if given, inside a subreddit within a time interval
    and returns the respective submission ids found. Pushshift API is used for searching.

    Parameters:

    keyword (str): keyword to search

    subreddit (str): subreddit title

    interval (tuple): interval object (tuple) representing starting timestamp and ending timestamp

    size (int) - optional: page size requested to the Pushshift API.

    Returns:

    list: a list of submission ids
    """
    keyword_query = f'&q={keyword}' if keyword is not None else ''
    if keyword is None:
        print(f'Searching without keywords...')
    
    request_url = f'{PUSHSHIFT_URL}?subreddit={subreddit}&after={interval[0]}&before={interval[1]}&size={size}&metadata=true{keyword_query}'
    print(request_url)

    response = requests.get(request_url)
    if response.status_code != 200 or response.text is None:
        raise Exception(response.text)
    
    response_json = response.json()

    if (response_json == None):
        return []

    return list(map(lambda submission: submission["id"], response_json["data"]))


def get_submissions_with_keywords_for_interval(subreddit, interval, keyword = None, size = 500):
    """Search for a keyword, if given, inside a subreddit within a time interval
    and returns the respective submission ids found. Pushshift API is used for searching.

    Parameters:

    keyword (str): keyword to search

    subreddit (str): subreddit title

    interval (tuple): interval object (tuple) representing starting timestamp and ending timestamp

    size (int) - optional: page size requested to the Pushshift API.

    Returns:

    list: a list of submissions
    """
    keyword_query = f'&q={keyword}' if keyword is not None else ''
    if keyword is None:
        print(f'Searching without keywords...')
    
    request_url = f'{PUSHSHIFT_URL}?subreddit={subreddit}&after={interval[0]}&before={interval[1]}&size={size}&metadata=true{keyword_query}'
    print(request_url)

    response = requests.get(request_url)
    if response.status_code != 200 or response.text is None:
        raise Exception(response.text)
    
    response_json = response.json()

    if (response_json == None):
        return []

    return response_json["data"]
