#!/usr/bin/env python3
# Program to automatically add all repositories from a GitHub account

import argparse
import json
import os
import sys
import requests
from urllib.parse import urlparse
from add_repo import add_repo, load_projects, save_projects, PROJECTS_DIR, DATA_FILE

def get_github_repos(username):
    """
    Get all repositories for a GitHub username using the GitHub API
    """
    url = f"https://api.github.com/users/{username}/repos"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        # Get all repositories, including those on next pages
        repos = response.json()
        
        # Check if there are more pages (GitHub API pagination)
        while 'next' in response.links.keys():
            response = requests.get(response.links['next']['url'], headers=headers)
            response.raise_for_status()
            repos.extend(response.json())
        
        return repos
    except requests.exceptions.RequestException as e:
        print(f"Error accessing GitHub API: {e}")
        return None

def add_account_repos(username, chat_url=None, localhost_url=None):
    """
    Add all repositories belonging to a GitHub username
    """
    # Ensure projects directory exists
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    
    # Get all repositories for the user
    print(f"Fetching repositories for GitHub user: {username}")
    repos = get_github_repos(username)
    
    if not repos:
        print(f"No repositories found or error accessing GitHub for user: {username}")
        return False
    
    # Process repositories
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    print(f"Found {len(repos)} repositories for {username}")
    
    for repo in repos:
        # Skip forks if they are private or archived
        if repo.get('fork', False) and (repo.get('private', False) or repo.get('archived', False)):
            print(f"Skipping fork: {repo['name']}")
            skip_count += 1
            continue
        
        # Get clone URL (prefer SSH if available)
        clone_url = repo.get('ssh_url') or repo.get('clone_url')
        if not clone_url:
            print(f"Skipping: No clone URL for {repo['name']}")
            skip_count += 1
            continue
        
        project_name = repo['name']
        print(f"\nProcessing: {project_name}")
        
        # Check if already in projects
        projects = load_projects()
        if project_name in projects:
            print(f"Skipping: Project '{project_name}' is already in the projects file")
            skip_count += 1
            continue
        
        # Add repository
        result = add_repo(clone_url, chat_url, localhost_url)
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\nSummary: Added {success_count} repositories, skipped {skip_count}, failed {fail_count}")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='Add all GitHub repositories from a user account')
    parser.add_argument('username', help='GitHub username')
    parser.add_argument('--chat-url', help='URL for chat application (default: https://chat.com)')
    parser.add_argument('--localhost-url', help='URL for localhost (default: http://localhost:3000)')
    
    args = parser.parse_args()
    
    # Default localhost URL if not provided
    localhost_url = args.localhost_url or "http://localhost:3000"
    
    # Add repositories
    success = add_account_repos(args.username, args.chat_url, localhost_url)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 