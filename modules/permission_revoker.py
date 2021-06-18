#!/usr/bin/env python3

# Defaults that were in quickstart.py (tutorial by Google)
# https://developers.google.com/drive/api/v3/quickstart/python
#from __future__ import print_function
#import pickle
#import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For checking object type isinstance(service, Resource)
from googleapiclient.discovery import Resource

# Replace text
import re
# JSON dumps
import json
# logging
# https://stackoverflow.com/questions/13733552/logger-configuration-to-log-to-file-and-print-to-stdout
# https://www.loggly.com/ultimate-guide/python-logging-basics/
import logging
#import logging.handlers
#import os
# Time stamps to files
from datetime import datetime
# For time.sleep()
import time
# logging into file and stdout
import sys
# Retrieve the name of current function
import inspect
# Try Catch HttpError
# https://stackoverflow.com/questions/23945784/how-to-manage-google-api-errors-in-python
from googleapiclient.errors import HttpError

from modules.create_creds import DriveService
from modules.conf_parser import ConfParser

# For deep copying a dict
# https://docs.python.org/3/library/copy.html
# https://stackoverflow.com/questions/2465921/how-to-copy-a-dictionary-and-only-edit-the-copy
import copy

class PermissionRevoker:
    """A class for revoking Google Drive user/domain permission from files."""

    def __init__(self, conf: ConfParser = None):

        if conf is not None and isinstance(conf, ConfParser):
            self.conf = conf
        else:
            self.conf = ConfParser()

        logging.info("Creating credential token")
        self.drive_service = DriveService()
        
	# This variable could be flipped true and wait could be triggered, when there's error of
        # exceeding traffic quota.
        self.over_quota_bool = False
        
	# full_json stores the whole Google file structure with additional information.
        self.full_json = []
        self.full_json_creation_error = False

	# If a full_json is created, the file path should be saved in this variable.
        self.created_full_json_path = ""
        
	# Stores file IDs and names of all checked files.
        self.all_checked_files_dict = {}
        
	# The user who is running the script to revoke permissions.
        self.current_user = self.get_current_user()
        
	# Adding special value to all_revoke_share_ids_dict, so that "empty" JSON is written out.
        self.all_revoke_share_ids_dict = dict({"empty_dict" : {"revoke_permissions": {
                "empty_permission" :
                {"the_only": "If this is the only one left, all other permissions have been removed."}}}})
        self.num_of_revoked_permissions = 0
        self.num_of_revoke_errors = 0
        self.is_there_something_to_revoke = False
        self.parent_list = None
        self.root_json_creation_error = False

    def create_full_json(self):
        """Creates a full_json JSON file and saves to disk.
        Creating a full_json file should be done as r

        Parameters
        ----------

        Returns
        -------
        list
            A list in JSON syntax. Content is all relevant information about
            Google Drive files/folders for revoking shares.
        """
        conf = self.conf
        service = self.drive_service.service

        logging.info("### Creating full_json")
        logging.info("Retrieving parent folder as JSON")
        # Creating a list of so it's easy loop the files afterwards.
        self.full_json = [self.get_json_of_one_google_file(self.conf.get_parent_id())]
        
        # Check if full_json is valid and there was no error.
        try:
            if self.full_json[0]["error"]["message"]:
                self.full_json_creation_error = True
                return
        except KeyError:
            pass

        logging.info("Adding children recursively")
        self.add_children_recursively(self.full_json)
        logging.info("All files in the retrieved list:")
        self.log_all_files(self.full_json)
        logging.info("Total number of files/folders including root folder: " +
                str(len(self.all_checked_files_dict)))
        logging.info("Saving full JSON file")
        full_json_path = self.write_json_dump(self.full_json, self.conf.get_parent_id())
        logging.info("### Finished full_json creation")

        # Set the conf to match path of full_json
        self.created_full_json_path = full_json_path

    def create_parent_dict(self):
        """Creates a list of parent IDs which then can be used to create full_jsons and revoke
        permissions."""

        logging.info("### Creating parent_id list")
        logging.info("Retrieving root folder as JSON")
        root_json = [self.get_json_of_one_google_file(self.conf.get_root_id())]
        
        # Check if root_json is valid and there was no error.
        try:
            if self.root_json[0]["error"]["message"]:
                self.root_json_creation_error = True
                return
        except KeyError:
            pass
        
        logging.info("Adding one level of children to root JSON")
        # Arguments: JSON, max_depth == how many leves, current_depth == start with 0
        # JSON is mandatory, but depths are not. If depths are not given the whole file tree under
        # the parent will be checked.
        self.add_children_recursively(root_json, 1, 0)
        logging.info("All files in the retrieved list:")
        
        parent_id_dict = dict()
        # Create one item to the dict, so it's not empty
        parent_id_dict["empty"] = {"name":"empty", "folder":False}
        
        # log_all_files adds all checked files to parent_id_dict
        self.log_all_files(root_json, parent_id_dict)
        # Remove the "empty" item
        del parent_id_dict["empty"]
        logging.info("Total number of files/folders including root folder: " +
                str(len(parent_id_dict)))
        logging.info("Saving root JSON file")
        root_json_path = self.write_json_dump(root_json, self.conf.get_root_id())
        logging.info("### Finished root_json creation")
        parent_dict_json_path = self.write_json_dump(parent_id_dict, "parent_id_dict_"
                + self.conf.get_root_id())
       
    def get_json_of_one_google_file(self, gfile: str = None):
        # gfile == Google Drive file/folder ID
        # For example:
        # https://drive.google.com/drive/folders/16mbbT12343ypAs81234sGyO3u9fgHkkp
        service = self.drive_service.service

        if not gfile and isinstance(gfile, str):
            logging.error("Func: {}, no Google Folder/File ID given.".format(inspect.stack()[0][3]))
            return

        if not service and isinstance(service, Resource):
            logging.error("Func: {}, no service object given.".format(inspect.stack()[0][3]))
            return

        # These fields are not retrieved if requesting user is not owner/editor, so it's important
        # to retrieve owners/me field.
        # permissions
        # permissionIds
        # sharingUser
        #
        # If user is not owner, capabilities field can determine if user is
        # commenter, editor or viewer.
        # canEdit => editor
        # canComment => commenter
        # cannot comment or edit => viewer
        #
        # cababilities/canShare == determines if the current user can revoke permissions.
        # Neither editor without sharing cabaility, commenter or viewer can revoke permissions.
        # 
        # try-except is required, because there will be error if shortcut's targetId is
        # unavailable.
        try:
            response = service.files().get(fileId=gfile, \
                    fields='id, \
                    name, \
                    parents, \
                    mimeType, \
                    kind, \
                    createdTime, \
                    modifiedTime, \
                    shared, \
                    shortcutDetails, \
                    permissions, \
                    owners/me, \
                    owners/displayName, \
                    owners/permissionId, \
                    owners/emailAddress, \
                    capabilities/canShare').execute()
        
            logging.info('Retrieved JSON data of: {} {}'.format(response['id'], response['name']))
        
        except HttpError as err:
            response = json.loads(err.content)
            logging.error(response["error"]["message"])
            return response

        finally:
            pass

        # Return the parent in a list as then other functions work for both parent
        # and children.
        return response

    def add_children_recursively(self,
            json_file: list = None,
            max_depth: int = None,
            cur_depth: int = None):
        """Recursive function, which sdds children files/folders to parent JSON.
        The function uses another get_children_as_json().
        Parameters
        ----------
        list
            JSON file. Starting JSON file has to be created with get_json_of_one_google_file().
        """
        service = self.drive_service.service

        # Check arguments
        if not json_file or not isinstance(json_file, list):
            logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
            return
        #if not json_file or not isinstance(json_file, list):
        #    logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
        #    return

	# gfile == Google file/folder ID
        for gfile in json_file:
            # Check that mimeType is folder and max_depth is less than
            if "mimeType" in gfile and gfile["mimeType"] == "application/vnd.google-apps.folder":

                # Check for depth
                #
                logging.error("Depths cur_depth {} max_depth {}".format(cur_depth, max_depth))
                # If no max_depth was given, we can traverse freely all children.
                # If max_depth was given, as long as its smaller than cur_depth we can continue.
                if max_depth and cur_depth and cur_depth >= max_depth:
                    logging.warning("There's still children files/folders, but max_depth" +
                            "was reached, so retrieving children was stopped.")
                    return
                
                # Add 1 to the current depth if cur_depth was given, meaning it's not None.
                if not cur_depth is None:
                    cur_depth += 1
                
                logging.info("Adding children of: {} {}".format(gfile["id"], gfile["name"]))

                # Add children to the JSON file
                gfile["children"] = self.get_children_json(gfile["id"])

                # Check if returned gfile["children"] exists and continue traversing recursively
                # if not empty. If max_depth is zero, don't traverse.
                if gfile["children"]:
                    # Call the function recursively with the added children list
                    self.add_children_recursively(gfile["children"], max_depth, cur_depth)
            
            else:
                logging.info("    Not a folder: {} {} {}".format(
                    gfile["id"], 
                    gfile["name"],
                    gfile["mimeType"]))
    
    def get_children_json(self, gfile: str = None):
        
	# Check arguments
        if not gfile or not isinstance(gfile, str):
            logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
            return

        service = self.drive_service.service

        # Replace the PARENT_ID between single quotes with the real parent_id given
        query = re.sub("PARENT_ID", gfile, "'PARENT_ID' in parents")

        # Resources:
        # https://developers.google.com/drive/api/v3/reference/files
        # Example for retrieving paged information:
        # https://developers.google.com/drive/api/v3/search-files
        page_token = None
        all_responses = []

        # These fields are not retrieved if requesting user is not owner/editor, so it's important
        # to retrieve owners/me field.
        # permissions
        # permissionIds
        # sharingUser
        #
        # If user is not owner, capabilities field can determine if user is
        # commenter, editor or viewer.
        # canEdit => editor
        # canComment => commenter
        # cannot comment or edit => viewer
        #
        # cababilities/canShare == determines if the current user can revoke permissions.
        # Neither editor without sharing cabaility, commenter or viewer can revoke permissions.
        while True:
            response = service.files().list(q=query,
                                             pageSize=1000,
                                             spaces='drive',
                                             fields='nextPageToken, \
                                                     files(id, \
                                                     name, \
                                                     parents, \
                                                     mimeType, \
                                                     kind, \
                                                     createdTime, \
                                                     modifiedTime, \
                                                     shared, \
                                                     shortcutDetails, \
                                                     permissions, \
                                                     owners/me, \
                                                     owners/displayName, \
                                                     owners/permissionId, \
                                                     owners/emailAddress, \
                                                     capabilities/canShare)', \
                                                     pageToken=page_token).execute()
            for f in response.get('files', []):
                # Process change
                logging.info('    Found a child: {} {}'.format(f['name'], f['id']))
            
            all_responses += response.get('files', [])
            page_token = response.get('nextPageToken', None)

            if page_token is None:
                break

        # Requires deepcopy, so changes can be made during looping.
        children_json = copy.deepcopy(all_responses)

        # Check if there's shortucs and if there are, add their targets.
        for gfile in all_responses:
            if "mimeType" in gfile and \
                    gfile["mimeType"] == "application/vnd.google-apps.shortcut":
                shortcut_target = self.get_json_of_one_google_file(gfile["shortcutDetails"]["targetId"])
                
                # Check if there was error "File not found".
                # find return -1 if substring not found.
                if "error" in shortcut_target and \
                        shortcut_target["error"]["message"].find("File not found") != -1:
                    logging.warning("    Probably shortcut's targetId file/folder has been " +
                        "either removed or current user doesn't have access to the file/folder.")
                else:
                    children_json.append(shortcut_target)

        return children_json

    def create_all_revoke_share_ids(self, json_file: list = None):
        """Recursive function. Retrieves all fileIDs of shared fileas and the permissionIDs which
        have access.

        Parameters
        ----------
        json_file : list
            A JSON file which has Google Drive file/folder structure information.
        """

        # Checks that arguments are correct.
        if not json_file or not isinstance(json_file, list):
            logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
            return

        # gfile means Google file/folder
        for gfile in json_file:
            # Check that there's share section in gfile and check it's true
            if "shared" in gfile and gfile["shared"]:

                # If the current user is NOT owner or editor with canShare capability,
                # the current user is not authorized to revoke shares.
                # Only owner or editor with sharing capability can revoke shares.
                # If there's no canShare capability, user is either editor without sharing
                # permission or reader/commenter.
                # reader/commenter can't revoke revoke a share.
                if not gfile["capabilities"]["canShare"]:
                    # Notice that can't use "continue" as the recursive part in the end of function
                    # would be skipped.
                    pass
                else:
                    # Temp permission dict for storing to be revoked permissions
                    tmp_perms = {gfile["id"] : {
                        "name" : gfile["name"],
                        "owner.me" : gfile["owners"][0]["me"],
                        "revoke_permissions" : {} }}
                    for permission in gfile["permissions"]:
                        # Don't try to revoke permission of an owner,
                        # that would be just waste of traffic quota.
                        # Domain doesn't have "deleted" property, so it needs to be excepted.

                        # The folders show "shared person symbol" even if the Web GUI doesn't show
                        # any share, so probably "deleted" shares need to be revoked also.
                        if permission["role"] != "owner" or permission["type"] == "domain":
                            logging.debug("    FileID: {} has permissionId: {}".format(gfile["id"],
                                permission["id"]))

                            # Domain share doesn't have same properties as real users
                            if permission["type"] == "domain":
                                tmp_perms[gfile["id"]]["revoke_permissions"].update(
                                        {permission["id"] : {"domain": permission["domain"],
                                            "role" : permission["role"]}
                                        })
                            # "anyone" type is special as the permissionId is "anyoneWithLink"
                            elif permission["type"] == "anyone":
                                tmp_perms[gfile["id"]]["revoke_permissions"].update(
                                        {permission["id"] : {"role" : permission["role"]}})
                            else:
                                tmp_perms[gfile["id"]]["revoke_permissions"].update(
                                        {
                                            permission["id"] : {"emailAddress" : permission["emailAddress"],
                                                "role" : permission["role"],
                                                "deleted" : permission["deleted"]
                                            }
                                        })

                    # If some permissions were added to the temp file, add it to
                    # the real revoking dict
                    if tmp_perms[gfile["id"]]["revoke_permissions"]:
                        self.all_revoke_share_ids_dict.update(tmp_perms)
                        self.is_there_something_to_revoke = True

            # Call the function recursively with children list
            if "children" in gfile and gfile["children"]:
                logging.debug("Checking folder ID: {}".format(gfile["id"]))
                self.create_all_revoke_share_ids(gfile["children"])

    def log_files_to_be_revoked(self):
        """Logs file IDs and file names that have permissions which are possible to revoke."""

        tmp_rev_dict = self.all_revoke_share_ids_dict

        if tmp_rev_dict:
            tmp_file_ids_names = ""
            for file_id, val_dict in tmp_rev_dict.items():
                if file_id != "empty_dict":
                    tmp_file_ids_names += "\n" + file_id + " \"" + val_dict["name"] + "\""
            logging.info("### Files that have permissions which are possible to revoke:" +
                    " (syntax: FileID   \"File Name\" ): {}".format(tmp_file_ids_names))
        else:
            logging.info("### No files to revoke!")

    def log_all_files(self, json_file: list = None, checked_files: dict = None):
        """Recursive function which prints and logs all children.

        Parameters
        ----------
        json_file : list
            A JSON file to check children from.
        """
        
        if checked_files == None:
            all_dict = self.all_checked_files_dict
        else:
            all_dict = checked_files

        # Check arguments
        if not json_file or not isinstance(json_file, list):
            logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
            return
        if all_dict is None or not isinstance(all_dict, dict):
            logging.error("Func: {}, no dict given.".format(inspect.stack()[0][3]))
            return

        for gfile in json_file:
            # The root should be always folder. Otherwise no reason to log
            # children.
            if "mimeType" in gfile and gfile["mimeType"] == "application/vnd.google-apps.folder":

                # Log found folder
                logging.info("    {} {}".format(gfile["id"], gfile["name"]))

                # Add folders to all_dict
                all_dict[gfile["id"]] = {"name": gfile["name"], "folder": True}

                # Call the function recursively with children list
                # if there's key "children" and it's not empty list.
                if "children" in gfile and gfile["children"]:
                    logging.info("    id: {} children: ".format(gfile["id"]))
                    self.log_all_files(gfile["children"], all_dict)
                else:
                    logging.info("        No children id: {}".format(gfile["id"]))
            else:
                logging.info("        id: {} name: {}".format(gfile["id"], gfile["name"]))

                # Add files to all_dict
                all_dict[gfile["id"]] = {"name": gfile["name"], "folder": False}

    def open_json(self, file_name: str = None):
        """Opens a JSON file.
        Parameters
        ----------
        str
            To be opened file with path.
        """

        if not file_name or not isinstance(file_name, str):
            logging.error("Func: {}, no file name given.".format(inspect.stack()[0][3]))
            return

        logging.info("Opening JSON file: " + file_name)
        json_file = ""
        try:
            with open(file_name, 'r') as f:
                json_file = json.load(f)
        except (IOError, IsADirectoryError) as e:
            logging.error(e)

        return json_file

    def get_json_dump(self, json_obj_file):
        """Function for creating pretty print JSON."""

        return json.dumps(json_obj_file, indent=4, ensure_ascii=False)

    def print_json_dump(self, json_obj: list = None):
        """Function for testing console prints."""

        print(json.dumps(json_obj, indent=4, ensure_ascii=False))

    def write_json_dump(self, json_obj: list = None, file_name: str = None):
        """Write a JSON dump to a given folder.

        Parameters
        ----------
        json_obj : list

        file_name : str

        Returns
        -------
        str
            Output dir + filename
        """

        output_path = self.conf.get_output_path()
        
        if not json_obj:
            logging.error("Func: {}, no JSON given.".format(inspect.stack()[0][3]))
            return
        # If no file name given, just use "no_name_given" as prefix.
        if not file_name:
            logging.warning("Func: {}, no file name given.".format(inspect.stack()[0][3]))
            file_name = "no_name_given_"

        file_out = output_path + file_name + "_" + \
                datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
        logging.info("    Writing JSON: " + file_out)
        
        with open(file_out, 'w') as outfile:
            json.dump(json_obj, outfile, indent=4, ensure_ascii=False)

        # Return the full path + file name
        return file_out

    def get_current_user(self):
        """Retrieves current user information from Google Drive API."""
        
        logging.info("Checking current user information")

        response = self.drive_service.service.about().get(fields='user').execute()
        logging.info('    Current user: {} permissionId: {}'.format(
            response["user"]["emailAddress"],
            response["user"]["permissionId"]))

        return response

    def wait_print(self, secs: int = None):
        """Function for making the program to wait between API calls, so that the traffic quota
        would not be exceeded."""
        
        if not secs:
            return
        
        secs = secs + 1
        for sec in range(1, secs):
            # flush=True, so that the time is printed.
            print(sec, end =" ", flush=True)
            time.sleep(1)
        print("\n")

    def revoke_one_file_permission(self, gfile: str = None, permission_id: str = None):
        """Revokes one share from one file/folder.
        
        Returns
        -------
        list
            JSON response if successful or not. Empty JSON means that the revoke was successful.
        """
        service = self.drive_service.service

        if not gfile or not isinstance(gfile, str):
            logging.error("Func: {}, no fileId given.".format(inspect.stack()[0][3]))
            return
        if not permission_id or not isinstance(permission_id, str):
            logging.error("Func: {}, no permissionId given.".format(inspect.stack()[0][3]))
            return

        logging.info('Revoking permission: FileId {} permissionId {}'.format(gfile, permission_id))
        try:
            # response is 204 without content if successful
            # This can be tested with:
            # https://developers.google.com/drive/api/v3/reference/permissions/delete
            response = service.permissions().delete(fileId=gfile, \
                    permissionId=permission_id).execute()
            logging.info('    Successfully revoked permission: FileId {} permissionId {}'.format(
                gfile, permission_id))
            self.num_of_revoked_permissions += 1
        except HttpError as err:
            # https://stackoverflow.com/questions/23945784/how-to-manage-google-api-errors-in-python
            response = json.loads(err.content)
            logging.error(response["error"]["message"])
            self.num_of_revoke_errors += 1
        finally:
            pass

        # If response is empty, the request was successful.
        return response

    def valid_for_revoke(self):
        """A helper function to check if permission revoking can start."""

        rev_files = None

        # If all_revoke_share_ids_dict has been initialized during this program run,
        # use the initialized all_revoke_share_ids_dict. Otherwise load from file.
        if not self.is_there_something_to_revoke:
            return
        # There's actually always at least 1 item in the dict
        elif len(self.all_revoke_share_ids_dict) > 1:
            rev_files = self.all_revoke_share_ids_dict
    
        #rev_files = self.open_json(self.conf.get_revoke_json_path())

        return rev_files

    def revocations_were_made(self, tmp_rev_dict: dict = None, file_name: str = None):
        """Helper function to process dict if revocations were made."""

        if not isinstance(tmp_rev_dict, dict):
            logging.error("Func: {}, no dict given.".format(inspect.stack()[0][3]))
            return
        
        ## Have to create a deepcopy for deleting keys. 
        rm_dict = copy.deepcopy(tmp_rev_dict)

        # Loop through the dictionary and remove any empty permissions
        for gfile in tmp_rev_dict:
            if not tmp_rev_dict[gfile]["revoke_permissions"]:
                logging.debug("Removing permissions section from dict as there are no " +
                    "permissions anymore in the section.")
                del rm_dict[gfile]
        
        # Point self.all_revoke_share_ids_dict to the changed/updated dict.
        self.all_revoke_share_ids_dict = rm_dict
        # If everything is unshared tmp_rev_dict, should have only 1 index.
        if len(self.all_revoke_share_ids_dict) == 1:
            logging.info("All possible shares should have been revoked!")
        self.write_json_dump(rm_dict, file_name + self.conf.get_parent_id())

    def handle_revoke_response(self,
            revoke_response: dict = None,
            permission: str = None,
            gfile: str = None,
            tmp_rev_dict: dict = None):

        """A helper function for handling revocation responses."""

        # Empty revoke_response means that revocation was successful.
        if not revoke_response:

            # Removing permission from dict because the revocation request was successful.
            del tmp_rev_dict[gfile]["revoke_permissions"][permission]

        # find returns -1 if substring not found.
        # This should check if known errors are found and remove gfile from tmp_rev_dict
        # if known error found.
        elif revoke_response and \
                revoke_response["error"]["message"].find("Permission not found") != -1 or \
                revoke_response["error"]["message"].find("File not found") != -1:

            # Those errors mean that the permission doesn't exist anymore, so the permission
            # can be removed from dict also.
            del tmp_rev_dict[gfile]["revoke_permissions"][permission]
        else:
            logging.error("Unhandled revoking error: " + revoke_response["error"]["message"])

    def revoke_deleted(self):
        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False

        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():

                # Revoke permissions from deleted users. Google Drive WebUI will show sharing icon
                # otherwise even if the file/folder doesn't have active shares.
                if "deleted" in info.keys() and info["deleted"]:

                    revoke_attempt = True

                    logging.debug("Revoking a permission of a deleted user: " +
                            gfile + " " + rev_files[gfile]["name"])
                    revoke_response = self.revoke_one_file_permission(gfile, permission)

                    # If revoke_response is empty, the revocation was successful.
                    self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)
        
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_deleted_")
    
    def revoke_email_list(self):
        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False
        
        # Retrieve information from configuration
        revoke_email_list = self.conf.get_revoke_email_list()

        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():
                # Revoke email addresses defined in configuration file
                # Don't revoke current user
                if permission != cur_user_perm and "emailAddress" in info.keys():
                    for email in revoke_email_list:
                        # permission in tmp_rev_dict[gfile]["revoke_permissions"] check is required
                        # so that it's known if the permissions has been revoked already. For example
                        # there could be multiple times same email address in config file.
                        if info["emailAddress"].lower() == email.lower() and \
                            permission in tmp_rev_dict[gfile]["revoke_permissions"]:
                
                            revoke_attempt = True
                
                            logging.debug("Revoking " +
                                    info["emailAddress"] +
                                    "from file: " +
                                    gfile + " " +
                                    rev_files[gfile]["name"])
                
                            revoke_response = self.revoke_one_file_permission(gfile, permission)
                
                            # If revoke_response is empty, the revocation was successful.
                            self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)
                
                            # Break out from the loop, because one email address can't have
                            # multiple different permissions on one file.
                            break
        
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_emails_")
    
    def revoke_email_domain_list(self):
        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False

        # Retrieve information from configuration
        revoke_email_domain_list = self.conf.get_revoke_email_domain_list()
        
        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():
                # Revoke email domains defined in configuration file
                # Don't revoke current user
                if permission != cur_user_perm and "emailAddress" in info.keys():
                    for email_d in revoke_email_domain_list:
                        if info["emailAddress"].lstrip().split('@')[1].lower() == email_d.lower() and \
                                permission in tmp_rev_dict[gfile]["revoke_permissions"]:
                            
                            revoke_attempt = True
                            
                            logging.debug("Revoking {} with email domain {} from file {}".format(
                                permission, email_d, rev_files[gfile]["name"]))

                            revoke_response = self.revoke_one_file_permission(gfile, permission)

                            # If revoke_response is empty, the revocation was successful.
                            self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)
 
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_email_domains_")
    
    def revoke_permission_list(self):
        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False

        # Retrieve information from configuration
        revoke_permission_list = self.conf.get_revoke_permission_list()

        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():
                # Revoke permissions defined in configuration file.
                # Don't revoke current user.
                if permission != cur_user_perm and \
                        permission in tmp_rev_dict[gfile]["revoke_permissions"]:

                    # Loop through the permissions that are wanted to be revoked and
                    # check if current permissions is on of them.
                    for rev_perm in revoke_permission_list:
                        if permission == rev_perm:

                            revoke_attempt = True

                            logging.debug("Revoking {} from file {} {}".format(
                                permission, gfile, rev_files[gfile]["name"]))

                            revoke_response = self.revoke_one_file_permission(gfile, permission)

                            # If revoke_response is empty, the revocation was successful.
                            self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)

                            # Check if the permission was domain and that was the only way for
                            # current user to revoke permissions. If the permission was from domain
                            # and current user doesn't have any permissions for the file anymore,
                            # the rest of the permissions should be removed from rev_files dict.
                            cur_user_has_still_access = False
                            if tmp_rev_dict[gfile]["owner.me"]:
                                cur_user_has_still_access = True

                            # Check that there are still permissions to revoke.
                            if tmp_rev_dict[gfile]["revoke_permissions"] and \
                                    not cur_user_has_still_access:
                                
                                # If the revoked permission was domain or anyoneWithLink and role
                                # was writer/editor, check that current user stil has revoker access
                                # to the Google file.
                                if "domain" in info or permission.lower() == "anyonewithlink" and \
                                        info["role"] == "writer":

                                    # Get the current user's Google domain.
                                    cur_user_email = self.current_user["user"]["emailAddress"]
                                    cur_user_domain = cur_user_email.lstrip().split('@')[1].lower()
                                    
                                    # Temp permission, temp info. The permission inspected above
                                    # has been deleted from tmp_rev_dict, so tmp_rev_dict needs to
                                    # be looped for obsolete gfiles/permissions.
                                    for tmp_p, tmp_i in \
                                        tmp_rev_dict[gfile]["revoke_permissions"].items():
                                        if tmp_p == cur_user_perm and tmp_i["role"] == "writer":
                                            cur_user_has_still_access = True
                                            # Current user has still writer role, so let's break.
                                            break
                                        # Check if the domain is same as current user and writer
                                        # role.
                                        elif "domain" in tmp_i and \
                                                tmp_i["domain"] == cur_user_domain and \
                                                tmp_i["role"] == "writer":
                                            cur_user_has_still_access = True
                                            break
                                        # Check if anyoneWithLink has writer/editor role.
                                        elif tmp_p.lower() == "anyonewithlink" and \
                                                tmp_i["role"] == "writer":
                                            cur_user_has_still_access = True
                                            break
                                    
                                    # If current user doesn't have access anymore, remove obsolete
                                    # files/permissions from revocation dict.
                                    if not cur_user_has_still_access:
                                        logging.debug("    Current user does not have revocation" +
                                                " access anymore for file: {}".format(gfile))
                                        del tmp_rev_dict[gfile]
                                    else:
                                        logging.debug("    Current user has still revocation access" +
                                                " for file: {}".format(gfile))


                            # Break out from the loop, because one file can't have multiple same
                            # permissions.
                            break
 
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_permissions_")

    def revoke_current_user(self):
        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False

        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():
                # Revoke current user if not owner.
                if permission == cur_user_perm and \
                        permission in tmp_rev_dict[gfile]["revoke_permissions"] and \
                        not tmp_rev_dict[gfile]["owner.me"]:

                    revoke_attempt = True

                    logging.debug("Revoking {} from file {} {}".format(
                        permission, gfile, rev_files[gfile]["name"]))

                    revoke_response = self.revoke_one_file_permission(gfile, permission)

                    # If revoke_response is empty, the revocation was successful.
                    self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)
 
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_current_user_")
    
    def revoke_all_except_current_user(self):

        rev_files = self.valid_for_revoke()
        
        # If there the validator function didn't return anything.
        if rev_files is None:
            logging.error("Func: {}, no JSON to revoke!".format(inspect.stack()[0][3]))
            return
       
        # Requires a deepcopy, otherwise there's error "dictionary changed size during iteration"
        tmp_rev_dict = copy.deepcopy(rev_files)

        # Current user information
        cur_user_perm = self.current_user["user"]["permissionId"]

        # This is just a temp variable to track if something was revoked/"attempted to revoke".
        # If nothing is changed, there's no need to write out an unchanged JSON.
        revoke_attempt = False

        # gfile == Google Drive file/folder's hash ID.
        # rev_files is a dict which keys are Google Drive file/folder hash IDs.
        # rev_files has been created with func create_all_revoke_share_ids()
        for gfile in rev_files:
            # info == information about the permission: user, domain, email, deleted, etc
            for permission, info in rev_files[gfile]["revoke_permissions"].items():
                
                # Revoke all except current user.
                #
                # Check that the gfile is not "empty_dict", dict key "empty_dict" is required,
                # so that the dict doesn't become completely empty.
                if permission != cur_user_perm and \
                        permission in tmp_rev_dict[gfile]["revoke_permissions"] and \
                        gfile != "empty_dict":

                    revoke_attempt = True

                    logging.debug("Revoking {} from file {} {}".format(
                        permission, gfile, rev_files[gfile]["name"]))

                    revoke_response = self.revoke_one_file_permission(gfile, permission)

                    # If revoke_response is empty, the revocation was successful.
                    self.handle_revoke_response(revoke_response, permission, gfile, tmp_rev_dict)
 
        # If revocations were made, remove the permission from dict.
        if revoke_attempt:
            self.revocations_were_made(tmp_rev_dict, "revoked_all_except_current_user_")
