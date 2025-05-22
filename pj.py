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
import add_account
from add_account import add_account_repos
import edit_project
from edit_project import select_status_option, set_project_status, change_project_status

def list_projects():
    """List all projects with colored output, grouped by status"""
    projects = load_projects()
    
    if not projects:
        print("No projects found")
        return
    
    # Define colors
    COLORS = {
        "in progress": "\033[1;32m",  # Bold Green
        "completed": "\033[1;36m",    # Bold Cyan
        "abandoned": "\033[1;31m",    # Bold Red
        "prototype": "\033[1;33m",    # Bold Yellow
        "other": "\033[1;35m",        # Bold Magenta
        "Not set": "\033[1;37m",      # Bold White
        "RESET": "\033[0m",           # Reset
        "HEADER": "\033[1;34m"        # Bold Blue for headers
    }
    
    # Group projects by status
    status_groups = {}
    for name, data in projects.items():
        status = data.get('metadata', {}).get('status', 'Not set')
        if status not in status_groups:
            status_groups[status] = []
        
        # Add project with its last accessed time (default to 0 if not present)
        last_accessed = data.get('metadata', {}).get('last_accessed', 0)
        status_groups[status].append((name, last_accessed))
    
    # Sort statuses with "in progress" first, then by name
    status_order = ["in progress", "prototype", "completed", "abandoned", "other", "Not set"]
    def status_sort_key(status):
        if status in status_order:
            return status_order.index(status)
        return len(status_order)
    
    sorted_statuses = sorted(status_groups.keys(), key=status_sort_key)
    
    print(f"{COLORS['HEADER']}Projects by Status:{COLORS['RESET']}")
    total_count = 0
    
    # Print projects grouped by status and sorted by last accessed time
    for status in sorted_statuses:
        projects_in_status = status_groups[status]
        if not projects_in_status:
            continue
            
        # Sort projects by last accessed time (newest first)
        projects_in_status.sort(key=lambda x: x[1], reverse=True)
        
        # Print status header with count
        status_color = COLORS.get(status, COLORS["other"])
        print(f"\n{status_color}{status.upper()} ({len(projects_in_status)}){COLORS['RESET']}")
        
        # Print projects in this status group
        for i, (name, _) in enumerate(projects_in_status, 1):
            print(f"  {i}. {status_color}{name}{COLORS['RESET']}")
            total_count += 1
    
    print(f"\n{COLORS['HEADER']}Total: {total_count} projects{COLORS['RESET']}")

def delete_project(project_name, delete_files=False):
    """Delete a project from the projects file and optionally delete its directory"""
    projects = load_projects()
    
    if project_name not in projects:
        print(f"Error: Project '{project_name}' not found")
        return False
    
    project_path = projects[project_name]['path']
    
    # Confirm deletion
    print(f"Project found: {project_name}")
    print(f"Path: {project_path}")
    
    if delete_files:
        confirm = input(f"Are you sure you want to delete the project AND ITS FILES? (y/N): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled")
            return False
        
        # Delete project directory if requested
        try:
            import shutil
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                print(f"Deleted project directory: {project_path}")
        except Exception as e:
            print(f"Error deleting project directory: {e}")
            return False
    else:
        confirm = input(f"Are you sure you want to remove this project from the projects list? (y/N): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled")
            return False
    
    # Remove from projects file
    del projects[project_name]
    save_projects(projects)
    print(f"Removed project '{project_name}' from projects list")
    
    return True

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
    parser.add_argument('--account', metavar='USERNAME', help='Add all repositories from a GitHub account')
    parser.add_argument('--delete', metavar='PROJECT', help='Delete a project from the projects list')
    parser.add_argument('--delete-files', action='store_true', help='Also delete project files when deleting a project')
    parser.add_argument('--status', metavar='PROJECT', help='Change the status of a project')
    
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
        projects = load_projects()

        if localhost_url is None:
            print("Select localhost URL option (use arrow keys and Enter):")
            localhost_url = select_localhost_option()
            
            # Update the project with the selected localhost URL
            projects[project_name]['workspace_config']['localhost_url'] = localhost_url
            save_projects(projects)
        
        # Add status to the project
        print("Select status for this project (use arrow keys and Enter):")
        set_project_status(project_name, projects)
        save_projects(projects)
        return 0
    
    # Handle --account USERNAME
    if args.account:
        # Use add_account functionality
        localhost_url = args.localhost_url or "http://localhost:3000"
        success = add_account_repos(args.account, args.chat_url, localhost_url)
        return 0 if success else 1
    
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
            result = add_repo(git_url, args.chat_url, localhost_url, repo_path)
            if result:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\nSummary: Added {success_count} repositories, skipped {skip_count}, failed {fail_count}")
        return 0 if fail_count == 0 else 1
    
    # Handle --delete PROJECT
    if args.delete:
        # Find the exact project name if partial match
        project_name = args.delete
        projects = load_projects()
        
        # Try exact match first
        if project_name not in projects:
            # Try partial match (case insensitive)
            matches = []
            query = project_name.lower()
            for name in projects:
                if query in name.lower():
                    matches.append(name)
            
            if not matches:
                print(f"No project matching '{project_name}' found")
                return 1
            
            if len(matches) == 1:
                project_name = matches[0]
                print(f"Found project: {project_name}")
            else:
                # Multiple matches - let user choose
                print("Multiple matching projects found:")
                for i, name in enumerate(matches, 1):
                    print(f"{i}. {name}")
                
                while True:
                    try:
                        choice = input("Enter number to select project (or 'q' to quit): ")
                        if choice.lower() == 'q':
                            return 0
                        
                        index = int(choice) - 1
                        if 0 <= index < len(matches):
                            project_name = matches[index]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(matches)}")
                    except ValueError:
                        print("Please enter a valid number")
        
        # Delete the project
        success = delete_project(project_name, args.delete_files)
        return 0 if success else 1
    
    # Handle --status PROJECT
    if args.status:
        # Find the exact project name if partial match
        project_name = args.status
        projects = load_projects()
        
        # Try exact match first
        if project_name not in projects:
            # Try partial match (case insensitive)
            matches = []
            query = project_name.lower()
            for name in projects:
                if query in name.lower():
                    matches.append(name)
            
            if not matches:
                print(f"No project matching '{project_name}' found")
                return 1
            
            if len(matches) == 1:
                project_name = matches[0]
                print(f"Found project: {project_name}")
            else:
                # Multiple matches - let user choose
                print("Multiple matching projects found:")
                for i, name in enumerate(matches, 1):
                    print(f"{i}. {name}")
                
                while True:
                    try:
                        choice = input("Enter number to select project (or 'q' to quit): ")
                        if choice.lower() == 'q':
                            return 0
                        
                        index = int(choice) - 1
                        if 0 <= index < len(matches):
                            project_name = matches[index]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(matches)}")
                    except ValueError:
                        print("Please enter a valid number")
        
        # Change the project status
        success = change_project_status(project_name, projects)
        return 0 if success else 1
    
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
    if not (args.list or args.add or args.all or args.project or args.account or args.delete or args.status):
        parser.print_help()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 