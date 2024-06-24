# How to run: 
# 1. Get your Github PAT and update the script, replace <YOUR_TOKEN> with your PAT
# 2. Run the script without and args

# Output: 
# several json files inside problem_search/yml_steps directory

import requests
import pandas as pd
import yaml
import json
from collections import defaultdict, Counter
import os

# Replace with your GitHub token
GITHUB_TOKEN = 
'<YOUR_TOKEN>'

# Load organizations and repositories from CSV
org_repo_df = pd.read_csv('../data/organizations_repositories.csv')
# Has the following columns: organization, repository, latest_commit_sha, 
time_of_data_collection

# Headers for GitHub API requests
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_workflow_files(repo):
    """Retrieve all workflow files in a given repository."""
    url = 
f'https://api.github.com/repos/{repo}/contents/.github/workflows'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [file['name'] for file in response.json() if 
file['name'].endswith('.yml')]
    print(f"Failed to get workflow files for {repo}: 
{response.status_code}")
    return []

def download_file_content(url):
    """Download the content of a file from a given URL."""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    print(f"Failed to download file content from {url}: 
{response.status_code}")
    return ''

def parse_yaml_content(content):
    """Parse YAML content from a string."""
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"Failed to parse YAML content: {e}")
        return {}

def analyze_step_consistency(org, repo_steps):
    """Analyze step consistency within the same organization's 
repositories."""
    step_counter = defaultdict(Counter)
    inconsistencies = defaultdict(list)

    # Collecting steps and their commands from all repos
    for repo, steps in repo_steps.items():
        for step in steps:
            if 'name' in step:
                step_name = step['name']
                command = step['run']
                step_counter[step_name][command] += 1

    # Finding inconsistencies
    for step_name, commands in step_counter.items():
        if len(commands) > 1:
            # Inconsistencies if the same step name has different commands
            for command, count in commands.items():
                inconsistencies[step_name].append({
                    'command': command,
                    'count': count,
                    'repos': [
                        repo for repo, steps in repo_steps.items()
                        if any(step['name'] == step_name and step['run'] 
== command for step in steps)
                    ]
                })

    return inconsistencies

def main():
    org_yaml_data = defaultdict(lambda: defaultdict(list))

    # Directory to save JSON files
    output_dir = '../problem_search/yml_steps'
    os.makedirs(output_dir, exist_ok=True)

    for _, row in org_repo_df.iterrows():
        repo = row['repository']
        org = repo.split('/')[0]
        print(f"Processing {repo}")

        workflow_files = get_workflow_files(repo)
        for yml_file in workflow_files:
            file_url = 
f'https://raw.githubusercontent.com/{repo}/master/.github/workflows/{yml_file}'
            file_content = download_file_content(file_url)
            if file_content:
                workflow_data = parse_yaml_content(file_content)

                for job_id, job in workflow_data.get('jobs', {}).items():
                    for step_index, step in enumerate(job.get('steps', 
[])):
                        step_name = step.get('name', step.get('run', 
f'Step {step_index + 1}'))
                        step_command = step.get('run', step.get('uses'))
                        
                        if step_command:
                            step_detail = {
                                'id': step_index + 1,
                                'name': step_name,
                                'run': step_command
                            }
                            org_yaml_data[org][repo].append(step_detail)
                        else:
                            print(f"Invalid step in {repo}: {step}")

    # Save to JSON
    with open(f'{output_dir}/org_repo_steps.json', 'w') as f:
        json.dump(org_yaml_data, f, indent=4)

    # Analyzing for each organization
    for org, repo_steps in org_yaml_data.items():
        inconsistencies = analyze_step_consistency(org, repo_steps)
        # Save to JSON
        with open(f'{output_dir}/{org}_analysis.json', 'w') as f:
            json.dump(inconsistencies, f, indent=4)

if __name__ == "__main__":
    main()

