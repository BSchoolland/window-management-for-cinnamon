#!/usr/bin/env python3
# Program to automatically add a repository to the projects directory as a "project"

import argparse
import json
import os
import subprocess
import sys
import termios
import tty
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

def get_key():
    """Get a single keypress from the user"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def select_localhost_option():
    """Interactive selector for localhost URL options"""
    options = ["localhost:3000", "none", "custom"]
    current = 0
    
    while True:
        # Clear line and print options
        sys.stdout.write("\r" + " " * 50 + "\r")
        for i, option in enumerate(options):
            if i == current:
                sys.stdout.write(f"→ {option}  ")
            else:
                sys.stdout.write(f"  {option}  ")
        sys.stdout.flush()
        
        # Get key press
        key = get_key()
        
        # Handle arrow keys
        if key == '\x1b':  # Escape sequence
            next_key = get_key()
            if next_key == '[':
                direction = get_key()
                if direction == 'A':  # Up arrow
                    pass  # Not used in horizontal selection
                elif direction == 'B':  # Down arrow
                    pass  # Not used in horizontal selection
                elif direction == 'C':  # Right arrow
                    current = (current + 1) % len(options)
                elif direction == 'D':  # Left arrow
                    current = (current - 1) % len(options)
        elif key == '\r':  # Enter key
            print()  # Move to next line
            selected = options[current]
            
            if selected == "custom":
                custom_port = input("Enter custom localhost port: ")
                try:
                    port = int(custom_port)
                    return f"http://localhost:{port}"
                except ValueError:
                    print("Invalid port. Using default port 3000.")
                    return "http://localhost:3000"
            elif selected == "none":
                return None
            else:
                return f"http://localhost:3000"
        elif key == '\x03':  # Ctrl+C
            raise KeyboardInterrupt

def add_repo(url, chat_url=None, localhost_url=None):
    """Clone a repository and add it to projects"""
    # Extract project name from URL
    project_name = url.split('/')[-1]
    if project_name.endswith('.git'):
        project_name = project_name[:-4]
    
    # Load existing projects
    projects = load_projects()
    
    # Check if project is already in the JSON file
    if project_name in projects:
        print(f"Error: Project '{project_name}' is already in the projects file")
        return False
    
    # Check if project directory already exists directly in Projects directory
    project_path = os.path.join(PROJECTS_DIR, project_name)
    
    # Check if project exists anywhere in the Projects directory structure
    found_project_path = None
    for root, dirs, files in os.walk(PROJECTS_DIR):
        if os.path.basename(root) == project_name and os.path.exists(os.path.join(root, '.git')):
            found_project_path = root
            break
    
    # If project exists elsewhere in the Projects directory
    if found_project_path:
        print(f"Found existing repository at: {found_project_path}")
        project_path = found_project_path
    # If project directory exists directly in Projects but isn't cloned
    elif os.path.exists(project_path):
        if not os.path.exists(os.path.join(project_path, '.git')):
            # Project dir exists but isn't a git repo
            try:
                subprocess.run(['git', 'clone', url, project_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error cloning repository: {e}")
                return False
        else:
            print(f"Using existing repository at: {project_path}")
    else:
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
    
    # Set chat URL (default to chatGPT)
    if not chat_url:
        chat_url = "https://chat.com"
    
    # Add to projects data
    project_config = {
        'path': project_path,
        'url': url,
        'added_date': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        'workspace_config': {
            # reserve workspace 1 for already open windows
            'cursor_workspace': 2, # IDE
            'github_workspace': 4, # github.com issues
            'chat_workspace': 5, # chatGPT folder or just chatGPT
            'github_url': github_url,
            'chat_url': chat_url
        }
    }
    
    # Add localhost config only if a URL was provided
    if localhost_url:
        project_config['workspace_config']['localhost_workspace'] = 3  # development server
        project_config['workspace_config']['localhost_url'] = localhost_url
    
    projects[project_name] = project_config
    save_projects(projects)
    
    print(f"Successfully added project: {project_name}")
    print(f"Project path: {project_path}")
    print(f"GitHub URL: {github_url}")
    if localhost_url:
        print(f"Localhost URL: {localhost_url}")
    else:
        print("No localhost URL configured")
    print(f"Chat URL: {chat_url}")
    
    return project_name

def find_git_repos(base_dir):
    """Recursively find all git repositories in a directory"""
    git_repos = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip the .git directory itself to avoid duplicate entries
        if '.git' in dirs:
            # This directory is a git repository
            git_repos.append(root)
            # Don't traverse into .git directories
            dirs.remove('.git')
            
    return git_repos

def get_git_remote_url(repo_path):
    """Get the remote URL for a git repository"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # If origin remote doesn't exist, try to get any remote
        try:
            result = subprocess.run(
                ['git', '-C', repo_path, 'remote'],
                capture_output=True, text=True, check=True
            )
            remotes = result.stdout.strip().split('\n')
            if remotes:
                result = subprocess.run(
                    ['git', '-C', repo_path, 'remote', 'get-url', remotes[0]],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add a git repository as a project')
    parser.add_argument('url', nargs='?', help='URL of the git repository to clone')
    parser.add_argument('--chat-url', help='URL for chat application (default: https://chat.com)')
    parser.add_argument('--localhost-url', help='URL for localhost (default: interactive selection)')
    parser.add_argument('--all', action='store_true', help='Add all git repositories in the Projects directory')
    args = parser.parse_args()
    
    # Ensure projects directory exists
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    
    if args.all:
        # Find all git repositories in the Projects directory
        print(f"Scanning {PROJECTS_DIR} for git repositories...")
        repos = find_git_repos(PROJECTS_DIR)
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for repo_path in repos:
            # Skip the directory containing projects.json itself
            if repo_path == PROJECTS_DIR:
                continue
                
            project_name = os.path.basename(repo_path)
            print(f"\nProcessing: {project_name} ({repo_path})")
            
            # Check if already in projects
            projects = load_projects()
            if project_name in projects:
                print(f"Skipping: Project '{project_name}' is already in the projects file")
                skip_count += 1
                continue
            
            # Get git remote URL
            git_url = get_git_remote_url(repo_path)
            if not git_url:
                print(f"Skipping: Unable to determine git URL for {repo_path}")
                skip_count += 1
                continue
            
            # Use default localhost:3000
            localhost_url = "http://localhost:3000"
            
            # Add repository (but don't clone since it already exists)
            result = add_repo(git_url, args.chat_url, localhost_url)
            if result:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\nSummary: Added {success_count} repositories, skipped {skip_count}, failed {fail_count}")
        sys.exit(0 if fail_count == 0 else 1)
    
    if not args.url:
        print("Error: Repository URL is required unless --all is specified")
        sys.exit(1)
    
    # Interactive selection for localhost URL if not provided
    localhost_url = args.localhost_url
    
    # Add repository
    project_name = add_repo(args.url, args.chat_url, localhost_url)
    if not project_name:
        sys.exit(1)
    if localhost_url is None:
        print("Select localhost URL option (use arrow keys and Enter):")
        localhost_url = select_localhost_option()
    # load project and add the localhost url
    projects = load_projects()
    projects[project_name]['workspace_config']['localhost_url'] = localhost_url
    save_projects(projects)