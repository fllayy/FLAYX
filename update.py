import requests, zipfile, os, shutil, argparse
from io import BytesIO

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
__version__ = "v0.7"

GITHUB_API_URL = "https://api.github.com/repos/fllayy/FLAYX/releases/latest"
FLAYX_URL = "https://github.com/fllayy/FLAYX/archive/"
IGNORE_FILES = [".env", ".git"]

class bcolors:
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'

def check_version(with_msg=False):
    """Check for the latest version of the project.

    Args:
        with_msg (bool): option to print the message.

    Returns:
        str: the latest version.
    """
    response = requests.get(GITHUB_API_URL)
    latest_version = response.json().get("name", __version__)
    if with_msg:
        msg = f"{bcolors.OKGREEN}Your bot is up-to-date! - {latest_version}{bcolors.ENDC}\n" if latest_version == __version__ else \
              f"{bcolors.WARNING}Your bot is not up-to-date! The latest version is {latest_version} and you are currently running version {__version__}\n. Run `python update.py -l` to update your bot!{bcolors.ENDC}\n"
        print(msg)
    return latest_version

def download_file(version=None):
    """Download the latest version of the project.

    Args:
        version (str): the version to download. If None, download the latest version.

    Returns:
        BytesIO: the downloaded zip file.
    """
    version = version if version else check_version()
    print(f"Downloading FLAYX version: {version}")
    response = requests.get(FLAYX_URL + version + ".zip")
    if response.status_code == 404:
        print(f"{bcolors.FAIL}Warning: Version not found!{bcolors.ENDC}")
        exit()
    print("Download Completed")
    return response

def install(response, version):
    """Install the downloaded version of the project.

    Args:
        response (BytesIO): the downloaded zip file.
        version (str): the version to install.
    """
    user_input = input(f"{bcolors.WARNING}--------------------------------------------------------------------------\n"
                           "Note: Before proceeding, please ensure that there are no personal files or\n"
                           "sensitive information in the directory you're about to delete. This action\n"
                           "is irreversible, so it's important to double-check that you're making the \n"
                           f"right decision. {bcolors.ENDC} Continue with caution? (y/n) ")
        
    if user_input.lower() in ["y", "yes"]:
        print("Installing ...")
        zfile = zipfile.ZipFile(BytesIO(response.content))
        zfile.extractall(ROOT_DIR)

        version = version.replace("v", "")
        source_dir = os.path.join(ROOT_DIR, f"FLAYX-{version}")
        if os.path.exists(source_dir):
            for filename in os.listdir(ROOT_DIR):
                if filename in IGNORE_FILES + [f"FLAYX-{version}"]:
                    continue

                filename = os.path.join(ROOT_DIR, filename)
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
            for filename in os.listdir(source_dir):
                shutil.move(os.path.join(source_dir, filename), os.path.join(ROOT_DIR, filename))
            os.rmdir(source_dir)
        print(f"{bcolors.OKGREEN}Version {version} installed Successfully! Run `python main.py` to start your bot{bcolors.ENDC}")
    else:
        print("Update canceled!")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Update script for FLAYX.')
    parser.add_argument('-c', '--check', action='store_true', help='Check the current version of the FLAYX')
    parser.add_argument('-v', '--version', type=str, help='Install the specified version of the FLAYX')
    parser.add_argument('-l', '--latest', action='store_true', help='Install the latest version of the FLAYX from Github')
    parser.add_argument('-b', '--beta', action='store_true', help='Install the beta version of the FLAYX from Github')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()

    if args.check:
        check_version(with_msg=True)
        
    elif args.version:
        version = args.version
        response = download_file(version)
        install(response, version)
        
    elif args.latest:
        response = download_file()
        version = check_version()
        install(response, version)
        
    elif args.beta:
        response = download_file("refs/heads/beta")
        install(response, "beta")
        pass

    else:
        print(f"{bcolors.FAIL}No arguments provided. Run `python update.py -h` for help.{bcolors.ENDC}")

if __name__ == "__main__":
    main()