#!/usr/bin/env python3
# Functions for editing project properties

import sys
import os
import json
import time
from pathlib import Path

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
        print(f"Warning: Projects data file not found at {DATA_FILE}")
        return {}

def save_projects(projects):
    """Save projects data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving projects: {e}")
        return False

def get_key():
    """Get a single keypress from the user"""
    import tty
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def select_status_option():
    """Interactive selector for project status options"""
    options = ["in progress", "completed", "abandoned", "prototype", "other"]
    current = 0
    
    while True:
        # Clear line and print options
        sys.stdout.write("\r" + " " * 80 + "\r")
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
            
            if selected == "other":
                custom_status = input("Enter custom status: ")
                return custom_status if custom_status else "other"
            else:
                return selected
        elif key == '\x03':  # Ctrl+C
            raise KeyboardInterrupt

def set_project_status(project_name, projects, status=None):
    """Set or update the status of a project"""
    if project_name not in projects:
        print(f"Error: Project '{project_name}' not found")
        return False
    
    if not status:
        print("Select status for this project (use arrow keys and Enter):")
        status = select_status_option()
    
    # Update the project with the selected status
    if 'metadata' not in projects[project_name]:
        projects[project_name]['metadata'] = {}
    
    projects[project_name]['metadata']['status'] = status
    save_projects(projects)
    print(f"Status for '{project_name}' set to: {status}")
    
    return True

def change_project_status(project_name, projects, save_projects_func=None):
    """Change the status of an existing project"""
    if project_name not in projects:
        print(f"Error: Project '{project_name}' not found")
        return False
    
    current_status = projects[project_name].get('metadata', {}).get('status', 'Not set')
    print(f"Current status for '{project_name}': {current_status}")
    
    print("Select new status (use arrow keys and Enter):")
    new_status = select_status_option()
    
    # Update the project with the selected status
    if 'metadata' not in projects[project_name]:
        projects[project_name]['metadata'] = {}
    
    projects[project_name]['metadata']['status'] = new_status
    
    # Use our own save function if none provided
    if save_projects_func is None:
        save_projects(projects)
    else:
        save_projects_func(projects)
        
    print(f"Status for '{project_name}' changed to: {new_status}")
    
    return True
