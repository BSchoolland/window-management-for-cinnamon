#!/usr/bin/env python3
# Program to delete a project from the projects.json file and optionally delete its directory

import argparse
import json
import os
import sys
import shutil

# Import functionality from existing scripts
from add_repo import load_projects, save_projects, PROJECTS_DIR, DATA_FILE

def find_project(query):
    """Find a project based on a partial name match"""
    projects = load_projects()
    
    if not projects:
        print("No projects found.")
        return None
    
    # Try exact match first
    if query in projects:
        return query, projects[query]
    
    # Try partial match (case insensitive)
    matches = []
    query = query.lower()
    for name, data in projects.items():
        if query in name.lower():
            matches.append((name, data))
    
    if not matches:
        print(f"No project matching '{query}' found")
        return None
    
    if len(matches) == 1:
        name, data = matches[0]
        print(f"Found project: {name}")
        return name, data
    
    # Multiple matches - let user choose
    print("Multiple matching projects found:")
    for i, (name, _) in enumerate(matches, 1):
        print(f"{i}. {name}")
    
    while True:
        try:
            choice = input("Enter number to select project (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(matches):
                name, data = matches[index]
                return name, data
            else:
                print(f"Please enter a number between 1 and {len(matches)}")
        except ValueError:
            print("Please enter a valid number")

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
    parser = argparse.ArgumentParser(description='Delete a project from the projects list')
    parser.add_argument('project', help='Name of the project to delete (partial name allowed)')
    parser.add_argument('--delete-files', action='store_true', help='Also delete project files')
    
    args = parser.parse_args()
    
    # Find the project
    result = find_project(args.project)
    if not result:
        return 1
    
    project_name, project_data = result
    
    # Delete the project
    success = delete_project(project_name, args.delete_files)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 