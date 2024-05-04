import requests
from requests.auth import HTTPBasicAuth
import json
import os



def load_credentials():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(dir_path + '/credentials.json'):
        with open('credentials.json') as json_file:
            data = json.load(json_file)

        return data

data = load_credentials()

email = data['email']
api_key = data['api_key']
BASE_URL = data['base_url']
project = data['project']
assignee = data['assignee']

AUTH = HTTPBasicAuth(email, api_key)


def get_request(request_url, request_headers, request_params=''):
    response = requests.request(
        "GET",
        request_url,
        headers=request_headers,
        params=request_params,
        auth=AUTH
    )
    if response.status_code != 400:
        return json.loads(response.text)
    else:
        print'failed - Could not access jira with credentials'

def post_request(request_url, headers, payload):
    response = requests.request(
        "POST",
        request_url,
        headers=headers,
        data=payload,
        auth=AUTH
    )

    if response.status_code == 400:
        print 'failed - Could not access jira with credentials'

def set_issue_status(issue_id, status_id):
    my_url = BASE_URL + "issue/{issueId}/transitions".format(issueId=issue_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }   

    payload = json.dumps( 
        {
            "transition": {
                "id": "{0}".format(status_id)
            }
        } 
    )

    post_request(my_url, headers, payload)

def log_time_against_issue(issue_id, time_spent, comment):
    my_url = BASE_URL + 'issue/{issueId}/worklog'.format(issueId=issue_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps( {
        "timeSpentSeconds": time_spent,
        "comment": {
            "type": "doc",
            "version": 1,
            "content": [
            {
                "type": "paragraph",
                "content": [
                {
                    "text": comment,
                    "type": "text"
                }
                ]
            }
            ]
        },
    } )
    print'Logging time against issue'
    post_request(my_url, headers, payload)
    print'Time logged'

def get_issue_comments(issue_id):
    my_url = BASE_URL +  'issue/{issueId}/comment'.format(issueId=issue_id)

    headers = {
        "Accept": "application/json"
    }

    return get_request(my_url, headers)

def post_comment(issue_id, comment, is_public_comment):
    my_url = BASE_URL + 'issue/{issueId}/comment'.format(issueId=issue_id)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps( {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
            {
                "type": "paragraph",
                "content": [
                {
                    "text": comment,
                    "type": "text"
                }
                ]
            }
            ]
        },
        "public": is_public_comment
    } )

    post_request(my_url, headers, payload)


def get_issue_transistions(issue_id):
    headers = {
        "Accept": "application/json"
    }

    my_url = BASE_URL + "issue/{issueId}/transitions".format(issueId=issue_id)

    return get_request(my_url, headers)

def get_issues_from_filter():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    query = {
        'jql': f'issuetype in (standardIssueTypes(), subTaskIssueTypes()) AND project in ({project}) AND assignee = "{assignee}" AND cf[10148] = Pipeline OR sprint in openSprints() AND project in ({project}) AND issuetype in (standardIssueTypes(), subTaskIssueTypes()) AND assignee = "{assignee}"',
        "maxResults": 100,
    }

    my_url = BASE_URL + '/search'
    return  get_request(my_url, headers, query)['issues']

def get_sprint_issues(team_code):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    query = {
        'jql': 'sprint in openSprints() AND project in ({0}) AND issuetype in (standardIssueTypes(), subTaskIssueTypes())'.format(team_code),
        "maxResults": 100,
    }

    my_url = BASE_URL + '/search'
    return  get_request(my_url, headers, query)['issues']

def get_all_issues(start_at):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    query = {
        'jql': f'issuetype in (standardIssueTypes(), subTaskIssueTypes()) AND project in ({project}) AND cf[10148] in (TEAM1, TEAM2, TEAM3) AND created >= "-60d" ORDER BY created DESC',
        'startAt': start_at,
        "maxResults": 100,
    }

    my_url = BASE_URL + '/search'
    return get_request(my_url, headers, query)['issues']

def get_all_issues_user_has_commented_on(username):
    relevant_issues = {}
    all_issues = []
    count = 0 
    for x in range(0, 10):
        all_issues.extend(get_all_issues(count))
        count += 100    

    for issue in all_issues:
        issue_comments = get_issue_comments(issue['id'])
        if issue_comments['comments']:
            for comment in issue_comments['comments']:
                if username in comment['author']['displayName']:
                    relevant_issues[issue['id']] = (issue, comment)
                    break

    return relevant_issues


