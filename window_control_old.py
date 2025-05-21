#!/usr/bin/env python3
import subprocess
import time
import re
import sys

def run_command(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.stderr.decode('utf-8')}")
        return ""

def get_window_pid(window_id):
    try:
        pid_info = run_command(f"xprop -id {window_id} _NET_WM_PID")
        pid = re.search(r'_NET_WM_PID\(CARDINAL\) = (\d+)', pid_info)
        if pid:
            return pid.group(1)
        return None
    except subprocess.CalledProcessError:
        return None

def get_window_id_number(window_id):
    """Convert window ID (like 0x02c0041d) to a number for comparison"""
    try:
        return int(window_id, 16)
    except ValueError:
        return 0

def get_window_creation_time(window_id):
    try:
        # Try to get the window's user time (activity timestamp)
        time_info = run_command(f"xprop -id {window_id} _NET_WM_USER_TIME")
        time_match = re.search(r'_NET_WM_USER_TIME\(CARDINAL\) = (\d+)', time_info)
        if time_match:
            return int(time_match.group(1))
    except subprocess.CalledProcessError:
        pass
    return 0

def get_ppid(pid):
    try:
        ppid = run_command(f"ps -o ppid= -p {pid}")
        return ppid.strip()
    except subprocess.CalledProcessError:
        return None

def is_ancestor(window_pid, shell_pid):
    """Check if window_pid is an ancestor of shell_pid by walking up the PPID chain"""
    current_pid = shell_pid
    visited_pids = set()  # Prevent infinite loops
    
    while current_pid and current_pid != "1" and current_pid not in visited_pids:
        visited_pids.add(current_pid)
        if current_pid == window_pid:
            return True
        current_pid = get_ppid(current_pid)
    
    return False

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
        
        # Make maximized instead of fullscreen
        run_command(f"wmctrl -i -r {window_id} -b remove,fullscreen")  # Remove fullscreen if set
        run_command(f"wmctrl -i -r {window_id} -b add,maximized_vert,maximized_horz")
        print(f"Moved window to workspace {workspace + 1}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to move window: {e}")
        return False

def make_window_fullscreen(window_id):
    """Make the window maximized"""
    try:
        # Remove fullscreen if set and add maximized state
        run_command(f"wmctrl -i -r {window_id} -b remove,fullscreen")
        run_command(f"wmctrl -i -r {window_id} -b add,maximized_vert,maximized_horz")
        print("Made window maximized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to make window maximized: {e}")
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

def run_and_move_window(command, workspace_number):
    # Get initial window list
    initial_windows = set(line.split()[0] for line in run_command("wmctrl -l").split('\n') if line)
    
    # Start the process
    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    
    # Wait for new window to appear
    new_windows = wait_for_new_window(initial_windows)
    if not new_windows:
        print(f"No new window found for: {command}")
        process.terminate()
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
        process.terminate()
        return False
    
    return True

def main():
    command = "google-chrome --new-window example.com"
    workspace = 4
    run_and_move_window(command, workspace)

if __name__ == "__main__":
    main() 