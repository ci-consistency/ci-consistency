import requests
import json
import pandas as pd
from datetime import datetime

# Constants
GITHUB_TOKEN = '<put your API token here>'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
BASE_URL = 'https://api.github.com'


def get_orgs_by_popularity():
    """Fetch organizations sorted by popularity (number of followers). This works fine"""
    orgs = []
    page = 1
    while len(orgs) < 300:
        url = f'{BASE_URL}/search/users?q=type:org&sort=followers&order=desc&per_page=3&page={page}'
        response = requests.get(url, headers=HEADERS).json()
        
        orgs.extend(response['items'])
        page += 1
    # Return the first 10 organizations
    return orgs[:3]

def check_repos_for_actions(org_login):
    """Check if the organization has at least 10 repositories using GitHub Actions."""
    url = f'{BASE_URL}/orgs/{org_login}/repos?type=public&per_page=100'
    repos = requests.get(url, headers=HEADERS).json()
    count = 0
    repo_with_actions=[]
    for repo in repos:
        # yml_file_html_urls=[]
        actions_url = f'{repo["url"]}/actions/workflows'        
        actions = requests.get(actions_url, headers=HEADERS).json()
        print(count)
        if actions.get('workflows'):
            print("*"*50)
            print(actions["workflows"])
            print("*"*50)
            repo_with_actions.append(repo["name"])
            count += 1
        if count >= 10:
            return True, repo_with_actions
    return False, []

def main():
    time_of_data_collection = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    orgs = get_orgs_by_popularity()
    data = []

    for org in orgs:
        org_have_enough_actions, repos_with_actions = check_repos_for_actions(org['login'])
        if org_have_enough_actions:
            data.append({
                'organization': org['login'],
                'repos_with_actions': "; ".join(repos_with_actions),
                'time_of_data_collection': time_of_data_collection
            })
        if len(data) == 110:
            break

    # Create a DataFrame from the collected data
    df = pd.DataFrame(data)
    df.to_csv('/home/tbaral/research/ci-consistency/logs/qualified_organizations.csv', index=False)

if __name__ == "__main__":
    main()