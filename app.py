import json
import os
import praw
from datetime import datetime
from src.db.dynamo import get_last_searched_date, save_last_searched_date
from src.parsers.reddit_parser import get_submission_data, get_subreddit_data, get_comments
from src.services.reddit_service import insert_comment, insert_submission, insert_subreddit
from src.integrations.pushshift import get_ids_from_submissions_with_keywords_for_interval
from src.utils.time_interval import get_timestamp_interval_for_starting_date


DEFAULT_COLLECTIONS = {
    'SUBMISSIONS': 'submissions',
    'COMMENTS': 'comments',
    'SUBREDDITS': 'subreddits',
}

DATE_FORMAT = '%Y-%m-%d'


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

        subreddit_submissions_map = {}

        for subreddit in params['subreddits']:
            submission_ids = set()

            print(f'Searching inside "{subreddit}" subreddit...')

            if len(params['keywords']) == 0:
                new_submission_ids = get_ids_from_submissions_with_keywords_for_interval(subreddit, interval)

                if (len(new_submission_ids) == 0): continue

                submission_ids = submission_ids.union(new_submission_ids)
            else:
                for keyword in params['keywords']:
                    print(f'Searching for "{keyword}" keyword...')

                    new_submission_ids = get_ids_from_submissions_with_keywords_for_interval(subreddit, interval, keyword)

                    if (len(new_submission_ids) == 0): continue

                    submission_ids = submission_ids.union(new_submission_ids)

            subreddit_submissions_map[subreddit] = list(submission_ids)


        all_ids = [sub_id for id_list in list(subreddit_submissions_map.values()) for sub_id in id_list]
        total_submissions = len(all_ids)
        print(f'{total_submissions} submissions found within the given date range')

        print(f'Starting gathering...')

        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'), 
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            password=os.getenv('REDDIT_PASSWORD'), 
            user_agent=os.getenv('REDDIT_USERAGENT'),
            username=os.getenv('REDDIT_USERNAME')
        )

        subreddits = list(subreddit_submissions_map.keys())
        for subreddit_id in subreddits:
            subreddit = reddit.subreddit(subreddit_id)

            if params['saveSubreddits']:
                print(f'Saving subreddits')
                subreddit_data = get_subreddit_data(subreddit)
                insert_subreddit(
                    subreddit_data, 
                    params['subredditsCollection']
                )

            submissions = subreddit_submissions_map[subreddit_id]
            no_of_submissions_in_subreddit = len(submissions)
            print(f'Gathering {no_of_submissions_in_subreddit} posts on "{subreddit.display_name}" subreddit')

            for submission_id in submissions:
                submission = reddit.submission(submission_id)

                submission_data = get_submission_data(submission)
                if submission_data is not None:
                    insert_submission(
                        submission_data,  
                        params['submissionsCollection']
                    )

                if params['saveComments']:
                    print(f'Saving comments')
                    comments = get_comments(submission)
                
                    for comment in comments:
                        insert_comment(
                            comment, 
                            params['commentsCollection']
                        )

        print(f'Posts gathered and saved')

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
