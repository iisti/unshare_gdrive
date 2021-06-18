# unshare_gdrive

* A Python project for revoking permissions from files/folders recursively from Google Drive.
* Unsharing a folder in Google Drive does not revoke permissions from files and folders inside the folder automatically. This feature makes managing big amounts of files and folders quite painful as when old team members change, soon nobody knows what is shared with whom. With this program whole folder can be unshared from certain email accounts and email domains.
* Google Drive has Team folders and managing those is easier than normal folders, but the subscription prices of these accounts are quite high.

* **THE DEVELOPER OF THIS PROGRAM DOES NOT TAKE ANY RESPONSIBILITY IF YOUR GOOGLE DRIVE IS MESSED UP!**
  * The program does not remove any files. Only permissions for accessing/editing files are removed.

# How to use
1. Install using the instructions below.
1. Create configuration file and edit it.
    
    ~~~
    cd unshare_gdrive
    cp config_example.conf config.conf
    
1. Run the program

    ~~~
    python3 unshare_gdrive.py -c config.conf
    ~~~
1. Examine contents of JSON file <parent_id>\_date-time.json in jsons folder for defining permissions to revoke, ie file name could be 16mbbTxxxxxxx_20210320-164010.json

# Installation/development instructions
* The development of this program has been mainly done with Windows Subsystem Linux, but the program should work with platforms that are able to run Python 3. 

### On Windows 10
1. Install WSL (Windows Subsystem Linux (the easiest way to use Linux in Windows)

### Installing Python3 and virtualenv on Debian WSL
1. Clone the repository
       
       git clone https://github.com/iisti/unshare_gdrive.git
1. Install Python3 and pip3

       sudo apt-get install python3 python3-pip
1. Install virtualenv using pip3

       sudo pip3 install virtualenv
1. Create virtual environment

       virtualenv unshare_gdrive/virtualenv
1. Activate virtual environment

       source unshare_gdrive/virtualenv/bin/activate
1. One can check which virtualenv is in use by:

       echo $VIRTUAL_ENV
       /home/iisti/scripts/unshare_gdrive/virtualenv
1. Deactivate (just to know how it's done)

       deactivate
       
1. Install modules
    ~~~
    # Remember to activate virtualenv before
    # docopt for using configuration files
    pip3 install docopt
    # Required Google modules
    pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    ~~~
1. Enable Drive API
   * Different options:
     1. **1st option:** Go to https://developers.google.com/drive/api/v3/quickstart/python and click **Enabe the Drive API**.
        * Using the quickstart link will set Oauth consent screen application text into "Quickstart", but it doesn't really matter.
        1. Set project name unshare-gdrive and click Next
        1. Configure your OAuth client: Desktop app
        1. Click Create
        1. Download the credential JSON file and name it credentials.json.
          * Put the credentials file to to path:
             * unshare_gdrive/credentials.json
     1. **2nd option:** Go to https://developers.google.com/drive/api/v3/enable-drive-api
          * Create **OAuth Client ID** credentials for API access. This is not tied to a certain real user. It's used to access the Google Project.
            * Application type: Desktop app
            * Name: unshare-gdrive-01
          * Download the credential JSON file and name it credentials.json.
          * Put the credentials file to to path:
             * unshare_gdrive/credentials.json
1. Configure configuration file
    ~~~
    # Copy the configuration file:
    cp config_example.conf config.conf
    
    # Edit config.conf with your favorite text editor.
    # For the first run configure at least:
    #    parent_id
    #    create_json
    # These settings will check the contents of the "parent_id" folder and
    # creates a JSON file which will contain all files/folders and permissions
    # of the "parent_id" folder's contents. 
    ~~~
1. Run the application, the first run should look something like this:
    ~~~
    python3 unshare_gdrive.py -c config.conf
    Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=845wwwwwwwwww73-1tinxxxxxxxxxxxxxxxd6rodr.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A44219%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&state=b1fYdTIxxxxHeSokqxxxYAxxxxx&access_type=offline

    # Copy paste the URL to browser and allow the application. If you used the first link when enabling Drive API the application name will be Quickstart, but it doesn't really matter. It could be changed in GCP -> project -> APIs & Services -> OAuth consent screen
    # Browser should give message: "The authentication flow has completed. You may close this window."
    ~~~
1. Output of the program should be something similar to:
~~~
2021-03-20 16:55:40,891 - INFO - Loaded configuration:
parent_id = 16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx
root_id = root
revoke_permission_id_list = 1234,123452,1245,anyone,anyoneWithLink
revoke_emails_list = user@domain.com
revoke_email_domain_list = email-domain.com
WARNING: full_json in conf file will be ignored as a new one will be created.
full_json = ./jsons/1uifPW343uUOWQyLmX-799pxxxxxxxxxx_20210114-221704.json
revoke_json_path = ./jsons/revoke_all_xxxxxxx.json
output_path = ./jsons/
log_path = ./logs/
create_json = true
revoke_deleted = false
revoke_emails = false
revoke_email_domains = false
revoke_permissions = false
revoke_current_user = false
revoke_all_except_current_user = false
revoke_from_json = false
revoke_with_root_id = false
log_level = info
2021-03-20 16:55:40,891 - INFO - Creating credential token
2021-03-20 16:55:40,894 - INFO - Checking current user information
2021-03-20 16:55:41,213 - INFO -     Current user: user.name@domain.com permissionId: 05834667599066666666
2021-03-20 16:55:41,214 - INFO - ### Creating full_json
2021-03-20 16:55:41,215 - INFO - Retrieving parent folder as JSON
2021-03-20 16:55:41,491 - INFO - Retrieved JSON data of: 16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx domain-logos
2021-03-20 16:55:41,491 - INFO - Adding children recursively
2021-03-20 16:55:41,492 - ERROR - Depths cur_depth None max_depth None
2021-03-20 16:55:41,493 - INFO - Adding children of: 16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx domain-logos
2021-03-20 16:55:41,947 - INFO -     Found a child: domain_logo_without_text 1TwlIOG4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,947 - INFO -     Found a child: domain_logo_without_text_a4 1A-z1qgxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,948 - INFO -     Found a child: domain_logo.png 1nRi6exxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,948 - INFO -     Found a child: domain_logo 1BB5oreOxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,948 - INFO -     Found a child: Untitled drawing 1kVSVed97xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,949 - INFO -     Found a child: Copy of domain-Logo_black_empInn-01-5720.png 1ILLM-zxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2021-03-20 16:55:41,950 - INFO -     Not a folder: 1TwlIOG4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx domain_logo_without_text application/vnd.google-apps.drawing
2021-03-20 16:55:41,950 - INFO -     Not a folder: 1A-z1qgxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx domain_logo_without_text_a4 application/vnd.google-apps.drawing
2021-03-20 16:55:41,951 - INFO -     Not a folder: 1nRi6exxxxxxxxxxxxxxxxxxxxxxxxx domain_logo.png image/png
2021-03-20 16:55:41,951 - INFO -     Not a folder: 1BB5oreOxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx domain_logo application/vnd.google-apps.drawing
2021-03-20 16:55:41,952 - INFO -     Not a folder: 1kVSVed97xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx Untitled drawing application/vnd.google-apps.drawing
2021-03-20 16:55:41,952 - INFO -     Not a folder: 1ILLM-zxxxxxxxxxxxxxxxxxxxxxxxxxxxx Copy of domain-Logo_black_empInn-01-5720.png image/png
2021-03-20 16:55:41,952 - INFO - All files in the retrieved list:
2021-03-20 16:55:41,953 - INFO -     16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx domain-logos
2021-03-20 16:55:41,953 - INFO -     id: 16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx children:
2021-03-20 16:55:41,953 - INFO -         id: 1TwlIOG4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx name: domain_logo_without_text
2021-03-20 16:55:41,953 - INFO -         id: 1A-z1qgxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx name: domain_logo_without_text_a4
2021-03-20 16:55:41,954 - INFO -         id: 1nRi6exxxxxxxxxxxxxxxxxxxxxxxxx name: domain_logo.png
2021-03-20 16:55:41,954 - INFO -         id: 1BB5oreOxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx name: domain_logo
2021-03-20 16:55:41,954 - INFO -         id: 1kVSVed97xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx name: Untitled drawing
2021-03-20 16:55:41,955 - INFO -         id: 1ILLM-zxxxxxxxxxxxxxxxxxxxxxxxxxxxx name: Copy of domain-Logo_black_empInn-01-5720.png
2021-03-20 16:55:41,955 - INFO - Total number of files/folders including root folder: 7
2021-03-20 16:55:41,955 - INFO - Saving full JSON file
2021-03-20 16:55:41,956 - INFO -     Writing JSON: ./jsons/16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx_20210320-165541.json
2021-03-20 16:55:41,960 - INFO - ### Finished full_json creation
2021-03-20 16:55:41,961 - INFO - ### Get files to be revoked
2021-03-20 16:55:41,962 - INFO -     Writing JSON: ./jsons/revoke_all_16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx_20210320-165541.json
2021-03-20 16:55:41,963 - INFO - Amount of possible permissions to be revoked: 7
2021-03-20 16:55:41,964 - INFO - ### Files that have permissions which are possible to revoke: (syntax: FileID   "File Name" ):
16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx "domain-logos"
1TwlIOG4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx "domain_logo_without_text"
1A-z1qgxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx "domain_logo_without_text_a4"
1nRi6exxxxxxxxxxxxxxxxxxxxxxxxx "domain_logo.png"
1BB5oreOxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx "domain_logo"
1kVSVed97xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx "Untitled drawing"
1ILLM-zxxxxxxxxxxxxxxxxxxxxxxxxxxxx "Copy of domain-Logo_black_empInn-01-5720.png"
2021-03-20 16:55:41,964 - INFO - The newly created full JSON: ./jsons/16mbbTxxxxxxxxxxxxxxxxxxxxxxxxxxx_20210320-165541.json
2021-03-20 16:55:41,965 - INFO - Number of revoke erros: 0
2021-03-20 16:55:41,965 - INFO - Number of revoked permissions: 0
~~~

## How to change user which is used for the revoking
* Move or remove **token.pickle** file.
