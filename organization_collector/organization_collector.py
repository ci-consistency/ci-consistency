import requests
import json
import pandas as pd
from datetime import datetime
import os

# Constants
GITHUB_TOKEN = 'Your Github Token'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
BASE_URL = 'https://api.github.com'

def get_orgs_by_popularity():
    """Fetch organizations sorted by popularity (number of followers) using fewer paginated requests."""
    orgs = []
    page = 1
    per_page = 100
    while len(orgs) < 300:
        url = f'{BASE_URL}/search/users?q=type:org&sort=followers&order=desc&per_page={per_page}&page={page}'
        response = requests.get(url, headers=HEADERS).json()
        
        # Handle errors by checking for "items" key
        if 'items' not in response:
            print("No 'items' key found in response. Possible rate limit exceeded or another issue.")
            break
        
        # Extend the list only if "items" is a list of dictionaries
        if isinstance(response['items'], list):
            orgs.extend(response['items'])
        else:
            print(f"Unexpected 'items' structure: {response['items']}")
        
        page += 1
    
    # Return the first 400 organizations or fewer if an error occurred
    return orgs[:300]

def check_repos_for_actions(org_login):
    """Check if the organization has at least 10 repositories using GitHub Actions and list all matching repos."""
    try:
        url = f'{BASE_URL}/orgs/{org_login}/repos?type=public&per_page=100'
        repos = requests.get(url, headers=HEADERS).json()
        
        # Confirm the response is a list
        if not isinstance(repos, list):
            print(f"Unexpected response for organization '{org_login}': {repos}")
            return False, []
        
        repo_with_actions = []
        for repo in repos:
            if not isinstance(repo, dict) or "url" not in repo or "name" not in repo:
                print(f"Skipping malformed repo data: {repo}")
                continue
            
            actions_url = f'{repo["url"]}/actions/workflows'
            actions = requests.get(actions_url, headers=HEADERS).json()
            
            if isinstance(actions, dict) and actions.get('workflows'):
                print(f"Repository '{repo['name']}' in organization '{org_login}' has GitHub Actions.")
                repo_with_actions.append(repo["name"])
            else:
                print(f"Unexpected response for actions in repo '{repo['name']}': {actions}")
        
        # Check if there are at least 10 repositories with GitHub Actions
        return len(repo_with_actions) >= 10, repo_with_actions
    except Exception as e:
        print(f"Error while checking repositories for organization '{org_login}': {e}")
        return False, []

def save_data(data, logs_dir, filename='qualified_organizations.csv'):
    """Save the collected data to a CSV file in the specified directory."""
    os.makedirs(logs_dir, exist_ok=True)
    output_path = os.path.join(logs_dir, filename)
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"CSV file was saved at: {output_path}")

def main():
    time_of_data_collection = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    orgs = get_orgs_by_popularity()
    data = []

    try:
        for org in orgs:
            if not isinstance(org, dict) or "login" not in org:
                print(f"Skipping malformed organization data: {org}")
                continue
            
            print(f"Processing organization: {org['login']}")
            org_have_enough_actions, repos_with_actions = check_repos_for_actions(org['login'])
            if org_have_enough_actions:
                data.append({
                    'organization': org['login'],
                    'repos_with_actions': "; ".join(repos_with_actions),
                    'time_of_data_collection': time_of_data_collection
                })
            if len(data) == 110:
                break
    except Exception as e:
        print(f"An error occurred during processing: {e}")

    # Save the collected data to a CSV file in the logs directory
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    save_data(data, logs_dir)

if __name__ == "__main__":
    main()
