import os
import subprocess
import requests
from gooey import Gooey, GooeyParser

GITHUB_REPO_OWNER = 'YourUsername'
GITHUB_REPO_NAME = 'YourRepository'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest'

@Gooey(dropdown_choices=['DFR', 'SI Multi-Tool', 'Program3', 'Program4', 'Program5'], program_name="Program Launcher and Updater", default_size=(600, 400))
def main():
    parser = GooeyParser(description="Select and launch programs")

    parser.add_argument('selected_program', widget='Dropdown', help="Select the program to launch", choices=['DFR', 'SI Multi-Tool', 'Program3', 'Program4', 'Program5'])
    args = parser.parse_args()

    program_name = args.selected_program

    # Check for updates
    latest_version = get_latest_version()
    current_version = get_installed_version(program_name)

    if latest_version and current_version < latest_version:
        print(f"Updating {program_name} to version {latest_version}...")
        download_and_update(program_name, latest_version)
        print(f"{program_name} updated successfully!")
    else:
        print(f"{program_name} is already up to date.")

    # Launch the selected program
    launch_program(program_name)

def get_latest_version():
    try:
        response = requests.get(GITHUB_API_URL)
        if response.status_code == 200:
            return response.json()['tag_name']
        else:
            print(f"Failed to fetch latest version: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching latest version: {e}")
    return None

def get_installed_version(program_name):
    # Implement logic to get the currently installed version of the program
    # Replace this with your own version retrieval mechanism
    return '1.0.0'

def download_and_update(program_name, version):
    # Implement logic to download and update the program to the specified version
    # Replace this with your own update mechanism
    pass

def launch_program(program_name):
    # Implement logic to launch the selected program
    # Replace this with your own program launch mechanism
    print(f"Launching {program_name}...")

if __name__ == '__main__':
    main()
