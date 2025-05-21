#!/usr/bin/env python3
# open a project in the projects directory

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECTS_DIR = "/home/ben/Projects"
DATA_FILE = os.path.join(PROJECTS_DIR, "projects.json")

def run_command(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.stderr.decode('utf-8')}")
        return ""

def ensure_workspace_exists(workspace_number):
    """Ensure the requested workspace exists, creating it if necessary"""
    try:
        # Get current number of workspaces
        current = int(run_command("gsettings get org.cinnamon.desktop.wm.preferences num-workspaces"))
        
        # If we need more workspaces, create them
        if workspace_number > current:
            run_command(f"gsettings set org.cinnamon.desktop.wm.preferences num-workspaces {workspace_number}")
            time.sleep(1)  # Give the system time to create the workspaces
            print(f"Created workspaces up to {workspace_number}")
        return True
    except Exception as e:
        print(f"Failed to ensure workspace exists: {e}")
        return False

def wait_for_new_window(initial_windows, max_attempts=20):
    """Wait for a new window to appear, returns set of new window IDs"""
    for attempt in range(max_attempts):
        try:
            current_windows = set(line.split()[0] for line in run_command("wmctrl -l").split('\n') if line)
            new_windows = current_windows - initial_windows
            if new_windows:
                return new_windows
            time.sleep(0.5)
        except Exception as e:
            print(f"Error checking windows (attempt {attempt}): {e}")
    return set()

def get_window_id_number(window_id):
    """Convert window ID (like 0x02c0041d) to a number for comparison"""
    try:
        return int(window_id, 16)
    except ValueError:
        return 0

def move_window_to_workspace(window_id, workspace):
    """Move window to specified workspace (0-based index)"""
    try:
        # Ensure the workspace exists
        if not ensure_workspace_exists(workspace + 1):
            return False
            
        # Activate the window first
        run_command(f"wmctrl -i -a {window_id}")
        time.sleep(0.5)
        
        # Move to workspace
        run_command(f"wmctrl -i -r {window_id} -t {workspace}")
        time.sleep(0.5)
        
        # Make maximized
        run_command(f"wmctrl -i -r {window_id} -b remove,fullscreen")  # Remove fullscreen if set
        run_command(f"wmctrl -i -r {window_id} -b add,maximized_vert,maximized_horz")
        print(f"Moved window to workspace {workspace + 1}")
        return True
    except Exception as e:
        print(f"Failed to move window: {e}")
        return False

def run_and_move_window(command, workspace_number):
    """Run a command and move its window to the specified workspace"""
    # Get initial window list
    initial_windows = set(line.split()[0] for line in run_command("wmctrl -l").split('\n') if line)
    
    # Start the process
    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    
    # Wait for new window to appear
    new_windows = wait_for_new_window(initial_windows)
    if not new_windows:
        print(f"No new window found for: {command}")
        return False
    
    # Find the window belonging to our process
    window_found = False
    for window_id in sorted(new_windows, key=get_window_id_number, reverse=True):
        if move_window_to_workspace(window_id, workspace_number - 1):
            print(f"Successfully moved window to workspace {workspace_number}")
            window_found = True
            break
    
    if not window_found:
        print(f"Failed to move window for: {command}")
        return False
    
    return True

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
        print(f"Warning: Projects data file not found at {DATA_FILE}")
        return {}

def find_project(query):
    """Find a project based on a partial name match"""
    projects = load_projects()
    
    if not projects:
        print("No projects found. Add a project first using add_repo.py")
        return None
    
    # Try exact match first
    if query in projects:
        return projects[query]
    
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
        return data
    
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
                return data
            else:
                print(f"Please enter a number between 1 and {len(matches)}")
        except ValueError:
            print("Please enter a valid number")

def open_project(project_data):
    """Open the selected project in configured applications and move to workspaces"""
    project_path = project_data['path']
    
    if not os.path.isdir(project_path):
        print(f"Error: Project directory not found: {project_path}")
        return False
    
    # Get workspace configurations or use defaults
    config = project_data.get('workspace_config', {})
    cursor_ws = config.get('cursor_workspace', 1)
    github_ws = config.get('github_workspace', 2)
    localhost_ws = config.get('localhost_workspace', 3)
    chat_ws = config.get('chat_workspace', 4)
    
    # Get URL configurations or use defaults
    github_url = config.get('github_url', project_data.get('url', '').replace('.git', '') + '/issues')
    localhost_url = config.get('localhost_url', 'http://localhost:3000')
    chat_url = config.get('chat_url', 'https://chat.openai.com')
    
    # Ensure we have all necessary workspaces
    max_workspace = max(cursor_ws, github_ws, localhost_ws, chat_ws)
    ensure_workspace_exists(max_workspace)
    
    success = True
    
    # Launch Cursor in workspace 1
    print(f"Opening project in Cursor at workspace {cursor_ws}...")
    cursor_cmd = f"cursor {project_path}"
    if not run_and_move_window(cursor_cmd, cursor_ws):
        success = False
        print("Failed to open Cursor, continuing with other applications...")
    
    # Launch GitHub Issues in workspace 2
    if github_url:
        print(f"Opening GitHub Issues at workspace {github_ws}...")
        github_cmd = f"google-chrome --new-window {github_url}"
        if not run_and_move_window(github_cmd, github_ws):
            success = False
            print("Failed to open GitHub Issues, continuing with other applications...")
    
    # Launch localhost in workspace 3
    if localhost_url:
        print(f"Opening localhost at workspace {localhost_ws}...")
        localhost_cmd = f"google-chrome --new-window {localhost_url}"
        if not run_and_move_window(localhost_cmd, localhost_ws):
            success = False
            print("Failed to open localhost, continuing with other applications...")
    
    # Launch chat in workspace 4
    if chat_url:
        print(f"Opening chat at workspace {chat_ws}...")
        chat_cmd = f"google-chrome --new-window {chat_url}"
        if not run_and_move_window(chat_cmd, chat_ws):
            success = False
            print("Failed to open chat, continuing with other applications...")
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Open a project from the projects directory')
    parser.add_argument('query', nargs='?', default='', help='Partial name of the project to open')
    args = parser.parse_args()
    
    if not args.query:
        print("Error: Project name or partial name is required")
        sys.exit(1)
    
    # Find and open project
    project_data = find_project(args.query)
    if project_data:
        success = open_project(project_data)
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)