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

# Import display function from edit_project.py
try:
    import edit_project
    from edit_project import display_project_info
    has_display_function = True
except ImportError:
    has_display_function = False

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
            time.sleep(0.25)  # Give the system time to create the workspaces
            print(f"Created workspaces up to {workspace_number}")
        return True
    except Exception as e:
        print(f"Failed to ensure workspace exists: {e}")
        return False

def get_windows_by_workspace():
    """Get a dictionary of windows organized by workspace"""
    windows_by_workspace = {}
    
    try:
        window_list = run_command("wmctrl -l")
        for line in window_list.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split(None, 3)
            if len(parts) >= 3:
                window_id = parts[0]
                workspace_num = int(parts[1])
                window_title = parts[3] if len(parts) > 3 else ""
                
                if workspace_num not in windows_by_workspace:
                    windows_by_workspace[workspace_num] = []
                    
                windows_by_workspace[workspace_num].append({
                    'id': window_id,
                    'title': window_title
                })
    except Exception as e:
        print(f"Error getting windows: {e}")
    
    return windows_by_workspace

def check_workspaces_have_windows(start_ws=2, end_ws=5):
    """Check if workspaces in the given range have any windows"""
    windows_by_workspace = get_windows_by_workspace()
    
    has_windows = False
    window_count = 0
    
    for ws in range(start_ws - 1, end_ws):
        if ws in windows_by_workspace and windows_by_workspace[ws]:
            has_windows = True
            window_count += len(windows_by_workspace[ws])
    
    return has_windows, window_count, windows_by_workspace

def close_windows_in_workspaces(start_ws=1, end_ws=4):
    """Close all windows in the specified workspace range"""
    windows_by_workspace = get_windows_by_workspace()
    
    closed_count = 0
    for ws in range(start_ws, end_ws + 1):
        if ws in windows_by_workspace:
            for window in windows_by_workspace[ws]:
                try:
                    # Close the window gracefully
                    run_command(f"wmctrl -ic {window['id']}")
                    closed_count += 1
                except Exception as e:
                    print(f"Error closing window {window['id']}: {e}")
    
    return closed_count

def minimize_unminimized_windows_in_workspaces(start_ws=1, end_ws=4):
    """Minimize all unminimized windows in the specified workspace range"""
    windows_by_workspace = get_windows_by_workspace()
    
    minimized_count = 0
    for ws in range(start_ws, end_ws + 1):
        if ws in windows_by_workspace:
            for window in windows_by_workspace[ws]:
                try:
                    # Use xdotool to minimize the window (more reliable than wmctrl)
                    result = run_command(f"xdotool windowminimize {window['id']}")
                    minimized_count += 1
                    print(f"Minimized window: {window['title']}")
                except Exception as e:
                    print(f"Error minimizing window {window['id']}: {e}")
    
    return minimized_count

def swap_window_visibility_in_workspaces(start_ws=1, end_ws=4):
    """Swap the visibility state of windows in the specified workspace range"""
    windows_by_workspace = get_windows_by_workspace()
    
    # Get current workspace to restore it later
    try:
        current_workspace = int(run_command("wmctrl -d | grep '*' | cut -d' ' -f1"))
    except:
        current_workspace = 0
    
    total_minimized = 0
    total_restored = 0
    
    print("Swapping window visibility by workspace...")
    
    # Process each workspace separately
    for ws in range(start_ws, end_ws + 1):
        if ws not in windows_by_workspace or not windows_by_workspace[ws]:
            continue
            
        workspace_windows = windows_by_workspace[ws]
        print(f"\nProcessing workspace {ws + 1} ({len(workspace_windows)} windows)...")
        
        # Switch to this workspace
        try:
            run_command(f"wmctrl -s {ws}")
            time.sleep(0.3)  # Give time for workspace switch
        except Exception as e:
            print(f"Error switching to workspace {ws + 1}: {e}")
            continue
        
        # Now check and swap windows in this workspace
        for window in workspace_windows:
            try:
                # Check if window is currently minimized by checking WM_STATE
                wm_state_output = run_command(f"xprop -id {window['id']} WM_STATE")
                
                # Parse the WM_STATE output
                is_minimized = False
                if "WM_STATE" in wm_state_output:
                    # Look for "Iconic" state - but only consider it minimized if we're on the right workspace
                    if "Iconic" in wm_state_output:
                        # Double-check by trying to see if window is actually visible
                        # Use xwininfo to check if window is mapped and viewable
                        wininfo = run_command(f"xwininfo -id {window['id']} | grep 'Map State'")
                        if "IsUnmapped" in wininfo or "IsUnviewable" in wininfo:
                            is_minimized = True
                        # If it's on current workspace and shows Iconic, it's likely minimized
                        elif "Iconic" in wm_state_output:
                            is_minimized = True
                
                if is_minimized:
                    # Window is minimized, restore it
                    run_command(f"xdotool windowactivate {window['id']}")
                    total_restored += 1
                    print(f"  Restored: {window['title']}")
                else:
                    # Window is visible, minimize it
                    run_command(f"xdotool windowminimize {window['id']}")
                    total_minimized += 1
                    print(f"  Minimized: {window['title']}")
                
                time.sleep(0.1)  # Small delay between operations
                
            except Exception as e:
                print(f"  Error processing window {window['id']}: {e}")
    
    # Return to original workspace
    try:
        run_command(f"wmctrl -s {current_workspace}")
        time.sleep(0.2)
    except Exception as e:
        print(f"Error returning to original workspace: {e}")
    
    print(f"\nCompleted: Minimized {total_minimized} windows, restored {total_restored} windows.")
    return total_minimized, total_restored

def wait_for_new_window(initial_windows, max_attempts=50):
    """Wait for a new window to appear, returns set of new window IDs"""
    for attempt in range(max_attempts):
        try:
            current_windows = set(line.split()[0] for line in run_command("wmctrl -l").split('\n') if line)
            new_windows = current_windows - initial_windows
            if new_windows:
                return new_windows
            time.sleep(0.2)
        except Exception as e:
            print(f"Error checking windows (attempt {attempt}): {e}")
    # if no new windows are found, print a warning
    print("Warning: No new windows found")
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
        
        # wait for the window to be found
        time.sleep(0.2)
        
        # Move to workspace
        run_command(f"wmctrl -i -r {window_id} -t {workspace}")
        time.sleep(0.2)
        
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

def open_project(project_data, close_windows=False):
    """Open the selected project in configured applications and move to workspaces"""
    project_path = project_data['path']
    
    if not os.path.isdir(project_path):
        print(f"Error: Project directory not found: {project_path}")
        return False
    
    # Get project name
    projects = load_projects()
    project_name = None
    for name, data in projects.items():
        if data['path'] == project_path:
            project_name = name
            break
    
    if project_name:
        # Display project info box using the shared function if available
        
        display_project_info(project_name, project_data)

        
        # Update last accessed time
        current_time = int(time.time())
        if 'metadata' not in projects[project_name]:
            projects[project_name]['metadata'] = {}
        projects[project_name]['metadata']['last_accessed'] = current_time
        
        # Save updated project data
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(projects, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to update last accessed time: {e}")
    
    # Check for existing windows in workspaces 2-5
    has_windows, window_count, _ = check_workspaces_have_windows(2, 5)
    
    if has_windows and close_windows:
        print(f"Found {window_count} windows in workspaces 2-5.")
        response = input("Close these windows and continue? (y/Enter to confirm, any other key to exit): ")
        
        if response.lower() != 'y' and response != '':
            print("Operation cancelled by user.")
            return False
        # Close windows in workspaces 2-5
        closed = close_windows_in_workspaces(1, 4) # 1-4 because index 0 is workspace 1
        print(f"Closed {closed} windows.")
        time.sleep(1)
    elif has_windows and not close_windows:
        # minimize the unminimized windows
        print("Minimizing unminimized windows...")
        minimized = minimize_unminimized_windows_in_workspaces(1, 4)
        print(f"Minimized {minimized} windows.")
        time.sleep(1)
    
    # automatically press "alt-f1" to open workspace view
    # Get workspace configurations or use defaults
    config = project_data.get('workspace_config', {})
    cursor_ws = config.get('cursor_workspace', 1)
    github_ws = config.get('github_workspace', 2)
    localhost_ws = config.get('localhost_workspace', 3)
    chat_ws = config.get('chat_workspace', 4)
    
    # Get URL configurations or use defaults
    github_url = config.get('github_url', project_data.get('url', '').replace('.git', '') + '/issues')
    localhost_url = config.get('localhost_url', 'http://localhost:3000')
    chat_url = config.get('chat_url', 'https://chat.com')
    
    # Ensure we have all necessary workspaces
    max_workspace = max(cursor_ws, github_ws, localhost_ws, chat_ws)
    ensure_workspace_exists(max_workspace)
    
    success = True
    
    # Launch Cursor in workspace 1
    print(f"Opening project in Cursor at workspace {cursor_ws} with nohup...")
    cursor_cmd = f"nohup cursor {project_path} > /dev/null 2>&1 & disown"
    if not run_and_move_window(cursor_cmd, cursor_ws):
        success = False
        print("Failed to open Cursor, continuing with other applications...")
    
    # Launch GitHub Issues in workspace 2
    if github_url:
        print(f"Opening GitHub Issues at workspace {github_ws}...")
        github_cmd = f"nohup google-chrome --new-window {github_url} > /dev/null 2>&1 & disown"
        if not run_and_move_window(github_cmd, github_ws):
            success = False
            print("Failed to open GitHub Issues, continuing with other applications...")
    
    # Launch localhost in workspace 3
    if localhost_url:
        print(f"Opening localhost at workspace {localhost_ws}...")
        localhost_cmd = f"nohup google-chrome --new-window {localhost_url} > /dev/null 2>&1 & disown"
        if not run_and_move_window(localhost_cmd, localhost_ws):
            success = False
            print("Failed to open localhost, continuing with other applications...")
    
    # Launch chat in workspace 4
    if chat_url:
        print(f"Opening chat at workspace {chat_ws}...")
        chat_cmd = f"nohup google-chrome --new-window {chat_url} > /dev/null 2>&1 & disown"
        if not run_and_move_window(chat_cmd, chat_ws):
            success = False
            print("Failed to open chat, continuing with other applications...")
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Open a project from the projects directory')
    parser.add_argument('query', nargs='?', default='', help='Name or Partial name of the project to open') 
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