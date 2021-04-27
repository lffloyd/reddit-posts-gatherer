import json
import os
import praw
from datetime import datetime
from src.db.dynamo import get_last_searched_date, save_last_searched_date
from src.parsers.reddit_parser import get_submission_data, get_subreddit_data, get_comments, get_submission_data_from_pushshift
from src.services.reddit_service import insert_comment, insert_submission, insert_subreddit
from src.integrations.pushshift import get_ids_from_submissions_with_keywords_for_interval, get_submissions_with_keywords_for_interval
from src.utils.time_interval import get_timestamp_interval_for_starting_date


DEFAULT_COLLECTIONS = {
    'SUBMISSIONS': 'submissions',
    'COMMENTS': 'comments',
    'SUBREDDITS': 'subreddits',
}

DATE_FORMAT = '%Y-%m-%d'


def get_all_submissions_from_intervals(subreddit, intervals, keyword = None, size = 500):
    """Search for a keyword inside a subreddit within time intervals
    and returns the respective submission ids found.

    Parameters:

    keyword (str): keyword to search

    subreddit (str): subreddit title

    intervals (list of tuple): list of interval objects (tuples) representing starting timestamp and ending timestamp

    size (int) - optional: page size requested to the Pushshift API.

    Returns:

    list: a list of submissions
    """
    submissions = []

    for interval in intervals:
        start_date = datetime.fromtimestamp(interval[0])
        end_date = datetime.fromtimestamp(interval[1])

        if start_date > end_date:
            continue

        print(f'Searching keyword within range ({start_date}, {end_date})...')

        new_submissions = get_submissions_with_keywords_for_interval(subreddit, interval, keyword)

        submissions = submissions + new_submissions

    return submissions


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    try:
        search_keywords = os.getenv('SEARCH_KEYWORDS')

        params = {
            'subreddits': os.getenv('SUBREDDITS').split(),
            'keywords': search_keywords.split('_') if search_keywords is not None else [],
            'start': os.getenv('START_DATE'),
            'end': os.getenv('END_DATE'),
            'saveComments': bool(int(os.getenv('SAVE_COMMENTS'))),
            'saveSubreddits': bool(int(os.getenv('SAVE_SUBREDDITS'))),
            'submissionsCollection': DEFAULT_COLLECTIONS['SUBMISSIONS'],
            'commentsCollection': DEFAULT_COLLECTIONS['COMMENTS'],
            'subredditsCollection': DEFAULT_COLLECTIONS['SUBREDDITS'],
            'daysPerInterval': int(os.getenv('DAYS_PER_INTERVAL')),
            'language': os.getenv('LANGUAGE'),
            'mongoDB': os.getenv('MONGO_DATABASE'),
        }
        print(f'Running on AWS ENV with params {params}')

        start_date = get_last_searched_date()

        max_end_date = datetime.strptime(params['end'], DATE_FORMAT)

        if start_date >= max_end_date:
            print(f'Start date is equal or bigger than maximum defined date: start_date - {start_date}, max_end_date - {max_end_date}')
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "nothing to do!",
                }),
            }

        interval = get_timestamp_interval_for_starting_date(start_date, max_end_date, params['daysPerInterval'])

        print(f'Starting search within {datetime.fromtimestamp(interval[0])} - {datetime.fromtimestamp(interval[1])} date range')

        count = 0

        for subreddit in params['subreddits']:
            submission_ids = set()

            print(f'Searching/gathering inside "{subreddit}" subreddit...')

            if len(params['keywords']) == 0:
                new_submissions = get_all_submissions_from_intervals(subreddit, interval)

                processed_submissions = list(map(lambda submission: get_submission_data_from_pushshift(submission), new_submissions))
                for submission in processed_submissions:
                    if submission is not None:
                        insert_submission(
                            submission, 
                            params['submissionsCollection']
                        )

                count += len(new_submissions)
            else:
                for keyword in params['keywords']:
                    print(f'Searching/gathering for "{keyword}" keyword...')

                    new_submissions = get_all_submissions_from_intervals(subreddit, interval, keyword)

                    processed_submissions = list(map(lambda submission: get_submission_data_from_pushshift(submission), new_submissions))
                    for submission in processed_submissions:
                        insert_submission(
                            submission, 
                            params['submissionsCollection']
                        )

                    count += len(new_submissions)

        print(f'{count} submissions found and collected with the given keywords ({", ".join(params["keywords"])})')

        last_searched_date = datetime.fromtimestamp(interval[1])
        save_last_searched_date(last_searched_date)

        print(f'Last searched date saved: {last_searched_date}')

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "finished successfully!",
            }),
        }
    except Exception as e:
        # Send some context about this error to Lambda Logs
        error_message = f'Error gathering posts: {e}'
        print(error_message)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": error_message,
            }),
        }
