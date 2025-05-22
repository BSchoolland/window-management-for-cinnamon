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

def select_filter_status():
    """Let the user select which status to filter by"""
    # Define status options
    options = ["in progress", "completed", "abandoned", "prototype", "other", "Not set"]
    
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
    
    print(f"\n{COLORS['HEADER']}Select status to filter projects by:{COLORS['RESET']}")
    
    for i, option in enumerate(options, 1):
        color = COLORS.get(option.lower(), COLORS["other"])
        print(f"{i}. {color}{option}{COLORS['RESET']}")
    
    while True:
        try:
            choice = input("\nEnter number (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(options):
                selected = options[index]
                print(f"\n{COLORS['HEADER']}Selected:{COLORS['RESET']} {COLORS.get(selected.lower(), COLORS['other'])}{selected}{COLORS['RESET']}")
                return selected
            else:
                print(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("Please enter a valid number")

def update_projects_by_status(filter_status=None):
    """Update all projects with a specific status"""
    # If no status provided, let user select one
    if not filter_status:
        filter_status = select_filter_status()
        if not filter_status:
            print("Operation cancelled.")
            return False
    
    projects = load_projects()
    
    # Find projects with the specified status
    matching_projects = []
    for name, data in sorted(projects.items()):
        status = data.get('metadata', {}).get('status', 'Not set')
        if status.lower() == filter_status.lower():
            # Add last accessed time for sorting
            last_accessed = data.get('metadata', {}).get('last_accessed', 0)
            matching_projects.append((name, data, last_accessed))
    
    if not matching_projects:
        print(f"No projects found with status: {filter_status}")
        return False
    
    # Sort by last accessed time (newest first)
    matching_projects.sort(key=lambda x: x[2], reverse=True)
    
    # Define colors
    COLORS = {
        "in progress": "\033[1;32m",  # Bold Green
        "completed": "\033[1;36m",    # Bold Cyan
        "abandoned": "\033[1;31m",    # Bold Red
        "prototype": "\033[1;33m",    # Bold Yellow
        "other": "\033[1;35m",        # Bold Magenta
        "not set": "\033[1;37m",      # Bold White
        "RESET": "\033[0m",           # Reset
        "HEADER": "\033[1;34m",       # Bold Blue for headers
        "HIGHLIGHT": "\033[1;33;44m"  # Yellow text on blue background
    }
    
    # Process each project
    total = len(matching_projects)
    updated = 0
    skipped = 0
    
    # Get color for the filter status
    filter_color = COLORS.get(filter_status.lower(), COLORS.get("other"))
    
    print(f"\n{COLORS['HEADER']}Updating projects with status: {filter_color}{filter_status}{COLORS['RESET']}")
    print(f"{COLORS['HEADER']}Found {total} matching projects{COLORS['RESET']}")
    print(f"\nPress 'Enter' to keep current status, arrow keys to change, 'q' to quit\n")
    
    for i, (name, data, _) in enumerate(matching_projects, 1):
        current_status = data.get('metadata', {}).get('status', 'Not set')
        current_color = COLORS.get(current_status.lower(), COLORS["other"])
        
        # Display project info
        print(f"{COLORS['HEADER']}Project {i}/{total}:{COLORS['RESET']} {current_color}{name}{COLORS['RESET']}")
        print(f"  Path: {data['path']}")
        print(f"  Current status: {current_color}{current_status}{COLORS['RESET']}")
        
        # Ask if user wants to update this project
        print("  Update status? [Enter to skip, arrow keys to select new status]")
        
        # Capture user input
        key = get_key()
        
        if key == '\r':  # Enter key - skip
            print(f"  {COLORS['HEADER']}Skipped{COLORS['RESET']}\n")
            skipped += 1
            continue
        elif key == 'q':  # Quit
            print(f"\n{COLORS['HEADER']}Operation cancelled. Updated {updated} projects, skipped {skipped} projects.{COLORS['RESET']}")
            return True
        elif key == '\x1b':  # Escape sequence for arrow keys
            # Let user choose new status
            print()  # Move to new line
            new_status = select_status_option()
            
            if new_status != current_status:
                # Update project status
                if 'metadata' not in projects[name]:
                    projects[name]['metadata'] = {}
                projects[name]['metadata']['status'] = new_status
                status_color = COLORS.get(new_status.lower(), COLORS["other"])
                print(f"  {COLORS['HEADER']}Updated status:{COLORS['RESET']} {current_color}{current_status}{COLORS['RESET']} → {status_color}{new_status}{COLORS['RESET']}\n")
                updated += 1
            else:
                print(f"  {COLORS['HEADER']}Status unchanged{COLORS['RESET']}\n")
                skipped += 1
        else:
            # Any other key - skip
            print(f"  {COLORS['HEADER']}Skipped{COLORS['RESET']}\n")
            skipped += 1
    
    # Save changes if any updates were made
    if updated > 0:
        save_projects(projects)
        print(f"\n{COLORS['HEADER']}Successfully updated {updated} projects, skipped {skipped} projects.{COLORS['RESET']}")
    else:
        print(f"\n{COLORS['HEADER']}No changes made. Skipped all {skipped} projects.{COLORS['RESET']}")
    
    return True
