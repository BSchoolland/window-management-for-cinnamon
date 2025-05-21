#!/usr/bin/env python3
# Command-line tool for managing projects

import argparse
import sys
import os
from pathlib import Path

# Import functionality from existing scripts
import add_repo
from add_repo import (
    add_repo, select_localhost_option, find_git_repos,
    get_git_remote_url, load_projects, save_projects, PROJECTS_DIR, DATA_FILE
)
import open_project
from open_project import find_project, open_project

def list_projects():
    """List all projects"""
    projects = load_projects()
    
    if not projects:
        print("No projects found")
        return
    
    print(f"Found {len(projects)} projects:")
    for name, data in sorted(projects.items()):
        print(f"  {name}: {data['path']}")

def main():
    # Ensure projects directory exists
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    
    parser = argparse.ArgumentParser(description='Project management tool')
    parser.add_argument('project', nargs='?', help='Partial name of the project to open')
    parser.add_argument('--add', metavar='URL', help='Add a git repository as a project')
    parser.add_argument('--chat-url', help='URL for chat application (default: https://chat.com)')
    parser.add_argument('--localhost-url', help='URL for localhost (default: interactive selection)')
    parser.add_argument('--all', action='store_true', help='Add all git repositories in the Projects directory')
    parser.add_argument('--list', action='store_true', help='List all projects')
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        list_projects()
        return 0
    
    # Handle --add URL
    if args.add:
        # Use add_repo functionality directly
        localhost_url = args.localhost_url
        
        project_name = add_repo(args.add, args.chat_url, localhost_url)
        if not project_name:
            return 1
            
        if localhost_url is None:
            print("Select localhost URL option (use arrow keys and Enter):")
            localhost_url = select_localhost_option()
            
            # Update the project with the selected localhost URL
            projects = load_projects()
            projects[project_name]['workspace_config']['localhost_url'] = localhost_url
            save_projects(projects)
            
        return 0
    
    # Handle --all
    if args.all:
        # Use add_repo's --all functionality
        # This simulates running add_repo.py with --all flag
        add_repo_args = argparse.Namespace()
        add_repo_args.all = True
        add_repo_args.url = None
        add_repo_args.chat_url = args.chat_url
        add_repo_args.localhost_url = args.localhost_url
        
        # Call the logic directly from the imported module
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
        return 0 if fail_count == 0 else 1
    
    # Handle opening a project by partial name
    if args.project:
        # Use find_project from open_project.py to find the project
        project_data = find_project(args.project)
        if project_data:
            # Use open_project from open_project.py to open the project
            success = open_project(project_data)
            return 0 if success else 1
        return 1
    
    # If no args, show usage
    if not (args.list or args.add or args.all or args.project):
        parser.print_help()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 