#!/usr/bin/env python3
# Program to automatically add a repository to the projects directory as a "project"

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECTS_DIR = "/home/ben/Projects"
DATA_FILE = os.path.join(PROJECTS_DIR, "projects.json")

def load_projects():
    """Load projects data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {DATA_FILE} is corrupted")
            return {}
    else:
        return {}

def save_projects(projects):
    """Save projects data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

def add_repo(url, chat_url=None, localhost_port=3000):
    """Clone a repository and add it to projects"""
    # Extract project name from URL
    project_name = url.split('/')[-1]
    if project_name.endswith('.git'):
        project_name = project_name[:-4]
    
    # Check if project directory already exists
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        print(f"Error: Project directory '{project_name}' already exists")
        return False
    
    # Clone the repository
    try:
        subprocess.run(['git', 'clone', url, project_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        return False
    
    # Create GitHub URL from git URL
    # Convert ssh URLs (git@github.com:user/repo.git) to https
    github_url = url
    if url.startswith('git@'):
        parts = url.split(':')
        if len(parts) == 2:
            domain = parts[0].split('@')[1]
            repo_path = parts[1]
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            github_url = f"https://{domain}/{repo_path}"
    
    # Handle direct HTTPS git URLs
    if github_url.endswith('.git'):
        github_url = github_url[:-4]
    
    # Add issues path if not present and it's a GitHub URL
    if 'github.com' in github_url and '/issues' not in github_url:
        github_url = f"{github_url}/issues"
    
    # Set localhost URL
    localhost_url = f"http://localhost:{localhost_port}"
    
    # Set chat URL (default to OpenAI chat)
    if not chat_url:
        chat_url = "https://chat.openai.com"
    
    # Add to projects data
    projects = load_projects()
    projects[project_name] = {
        'path': project_path,
        'url': url,
        'added_date': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        'workspace_config': {
            'cursor_workspace': 1,
            'github_workspace': 2,
            'localhost_workspace': 3,
            'chat_workspace': 4,
            'github_url': github_url,
            'localhost_url': localhost_url,
            'chat_url': chat_url
        }
    }
    save_projects(projects)
    
    print(f"Successfully added project: {project_name}")
    print(f"Project path: {project_path}")
    print(f"GitHub URL: {github_url}")
    print(f"Localhost URL: {localhost_url}")
    print(f"Chat URL: {chat_url}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add a git repository as a project')
    parser.add_argument('url', help='URL of the git repository to clone')
    parser.add_argument('--chat-url', help='URL for chat application (default: https://chat.openai.com)')
    parser.add_argument('--localhost-port', type=int, default=3000, help='Port number for localhost (default: 3000)')
    args = parser.parse_args()
    
    if not args.url:
        print("Error: Repository URL is required")
        sys.exit(1)
    
    # Ensure projects directory exists
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    
    # Add repository
    success = add_repo(args.url, args.chat_url, args.localhost_port)
    sys.exit(0 if success else 1)