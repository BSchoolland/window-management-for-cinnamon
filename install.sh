#!/bin/bash
# Installation script for the pj command-line tool

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a directory for the scripts in a standard location
INSTALL_DIR="/usr/local/lib/pj"
echo "Creating installation directory at $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"

# Copy all required Python files to the installation directory
echo "Copying scripts to installation directory..."
sudo cp "$SCRIPT_DIR/pj.py" "$INSTALL_DIR/pj.py"
sudo cp "$SCRIPT_DIR/add_repo.py" "$INSTALL_DIR/add_repo.py"
sudo cp "$SCRIPT_DIR/open_project.py" "$INSTALL_DIR/open_project.py"

# Make sure all Python files are executable
echo "Setting permissions..."
sudo chmod +x "$INSTALL_DIR/pj.py"
sudo chmod +x "$INSTALL_DIR/add_repo.py" 
sudo chmod +x "$INSTALL_DIR/open_project.py"

# Create a symbolic link to pj.py in /usr/local/bin/pj
echo "Creating symbolic link in /usr/local/bin/pj..."
sudo ln -sf "$INSTALL_DIR/pj.py" /usr/local/bin/pj

# Check if installation was successful
if [ -L /usr/local/bin/pj ] && [ -d "$INSTALL_DIR" ]; then
    echo "Installation successful! You can now use the 'pj' command."
    echo "Usage examples:"
    echo "  pj project_name  - Open a project matching the name"
    echo "  pj --add URL     - Add a git repository as a project"
    echo "  pj --all         - Add all git repositories in the Projects directory"
    echo "  pj --list        - List all projects"
else
    echo "Installation failed. Please check permissions and try again."
fi 