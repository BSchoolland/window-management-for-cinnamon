# Project Manager (pj)

A command-line tool for managing your development projects. This tool provides easy access to your coding projects, handling repository setup and workspace management.

## Features

- Open projects easily by typing partial names
- Automatically set up workspaces with IDE, GitHub issues, localhost, and chat
- Add Git repositories as projects
- Automatically detect and add all Git repositories in your Projects directory
- List all available projects

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/project-manager.git
   cd project-manager
   ```

2. Run the installation script:
   ```
   chmod +x install.sh
   ./install.sh
   ```

The installation script will:
- Create a directory at `/usr/local/lib/pj` to store the scripts
- Copy all required Python files to this directory
- Create a symbolic link at `/usr/local/bin/pj` to make the command available system-wide

## Usage

### Open a project
```
pj project_name
```
This will:
- Open the project matching the name (partial matching supported)
- Set up workspaces in Cinnamon with:
  - IDE (Cursor) in workspace 2
  - GitHub issues in workspace 4
  - Localhost (development server) in workspace 3
  - Chat application in workspace 5

### Add a Git repository
```
pj --add https://github.com/username/repo.git
```
This will:
- Clone the repository (if not already present)
- Add it to your projects list
- Configure workspace settings

### Add all Git repositories in Projects directory
```
pj --all
```
This will:
- Scan your Projects directory for Git repositories
- Add all found repositories to your projects list
- Configure workspace settings for each

### List all projects
```
pj --list
```
This will show a list of all registered projects and their locations.

## Configuration

Projects are stored in `~/Projects/projects.json`. The format is:

```json
{
  "project_name": {
    "path": "/home/user/Projects/project_name",
    "url": "https://github.com/username/repo.git",
    "added_date": "2023-05-15 14:30:22",
    "workspace_config": {
      "cursor_workspace": 2,
      "github_workspace": 4,
      "chat_workspace": 5,
      "github_url": "https://github.com/username/repo/issues",
      "chat_url": "https://chat.com",
      "localhost_workspace": 3,
      "localhost_url": "http://localhost:3000"
    }
  }
}
```

## Requirements

- Linux with Cinnamon desktop environment
- Python 3.6+
- wmctrl (for window management)
- Git (for repository operations)

## License

MIT 