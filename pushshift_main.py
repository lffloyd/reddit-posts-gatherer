from dotenv import load_dotenv
load_dotenv()

import argparse
import os
from datetime import datetime
from src.parsers.reddit_parser import get_comment_data, get_submission_data_from_pushshift
from src.services.reddit_service import insert_submission
from src.integrations.pushshift import get_submissions_with_keywords_for_interval
from src.utils.time_interval import get_timestamps_interval


DEFAULT_COLLECTIONS = {
    'SUBMISSIONS': 'submissions'
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


parser = argparse.ArgumentParser(description='Gather Reddit submission data and sends to cloud database.')

parser.add_argument('--subreddits', nargs='+', help='subreddits to gather', required=True)
parser.add_argument('--keywords', nargs='+', help='keywords to search for on the subreddit', required=False, default=None)
parser.add_argument('--start', type=str, help='gather posts written after this date', required=True)
parser.add_argument('--end', type=str, help='gather posts written before this date', required=True)
parser.add_argument('--submissionsCollection', type=str, help='MongoDB collection to save submissions', required=False, default=DEFAULT_COLLECTIONS['SUBMISSIONS'])
parser.add_argument('--daysPerInterval', type=float, help='no. of days per search interval', required=False)

args = parser.parse_args()
params = {
    'subreddits': args.subreddits,
    'keywords': args.keywords if args.keywords is not None else [],
    'start': args.start,
    'end': args.end,
    'submissionsCollection': args.submissionsCollection,
    'daysPerInterval': args.daysPerInterval,
    'mongoDB': os.getenv('MONGO_DATABASE'),
}
print(f'Running on local ENV with params {params}')

startDate = datetime.strptime(params['start'], DATE_FORMAT)
endDate = datetime.strptime(params['end'], DATE_FORMAT)
days = params['daysPerInterval']
timestampsInterval = list(get_timestamps_interval(startDate, endDate, days_per_interval=days) \
    if days is not None else get_timestamps_interval(startDate, endDate))

print(f'Starting searching/gathering...')

count = 0

for subreddit in params['subreddits']:

    print(f'Searching/gathering inside "{subreddit}" subreddit...')

    if len(params['keywords']) == 0:
        new_submissions = get_all_submissions_from_intervals(subreddit, timestampsInterval)

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

            new_submissions = get_all_submissions_from_intervals(subreddit, timestampsInterval, keyword)

            processed_submissions = list(map(lambda submission: get_submission_data_from_pushshift(submission), new_submissions))
            for submission in processed_submissions:
                insert_submission(
                    submission, 
                    params['submissionsCollection']
                )

            count += len(new_submissions)


print(f'{count} submissions found and collected with the given keywords ({", ".join(params["keywords"])}) and within the date range ({startDate.date()}, {endDate.date()})')

with open('gatherer_logs.txt', 'a+') as file:
    file.write(f'PUSHSHIFT SUBMISSIONS GATHERING - Date range: {startDate} - {endDate}\tTotal submissions: {count}\n')
