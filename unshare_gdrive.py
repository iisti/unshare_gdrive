#!/usr/bin/env python3

"""Unshare Google Drive

This is a Python program for unsharing Google Drive directories and files
recursively.

Usage:
    ugdrive.py (-c <FILE> | --config <FILE>)
    ugdrive.py (-h | --help)
    ugdrive.py --version

Options:
    -h --help   Show this screen.
    --version   Show version.
    -c --config Configuration file.

"""

# -*- coding: utf-8 -*-
# For documentation
from docopt import docopt

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
import logging.handlers
import os
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
from modules.permission_revoker import PermissionRevoker

# For deep copying a dict
# https://docs.python.org/3/library/copy.html
# https://stackoverflow.com/questions/2465921/how-to-copy-a-dictionary-and-only-edit-the-copy
import copy

def main():
    arguments = docopt(__doc__, version='Unshare Google Drive 0.1')
    config = ConfParser()
    config.load_ini_conf(arguments["--config"])

    # Create log file
    log_to_file(config, config.get_parent_id())
    logging.info("Loaded configuration: \n" + config.get_conf_str())

    revoker = PermissionRevoker(config)

    create_json = config.get_create_json_bool()
    revoke_with_root_id = config.get_revoke_with_root_id_bool()
    revoke_with_json = config.get_revoke_with_json_bool()

    # This is checked in function revoke_id() before revocation operation.
    revoke_nothing = config.get_revoke_nothing_bool()
    if revoke_nothing:
        logging.warning("Configuration file has setting revoke_nothing = True, nothing will be revoked.")

    # Check that only one of the variables above is True as otherwise there's
    # conflict.
    if sum([create_json, revoke_with_root_id, revoke_with_json]) > 1:
        logging.error("There is a conflict in the configuration file.\n"
            + "Only one of the options create_json, revoke_with_root_id, and revoke_with_json can be True.")

    if revoke_with_root_id:
        revoker.create_parent_dict()

        # Check if parent dict creation was successfull.
        if not revoker.root_json_creation_error:
            # Create copy and delete root_id.
            tmp_parent_dict = copy.deepcopy(revoker.parent_id_dict)
            tmp_parent_dict.pop(config.get_root_id(), None)
 
            # Iterate through the parent ID dictionary and revoke permissions.
            for k in tmp_parent_dict:
                revoke_id(config, k)
        else:
            logging.error("Creation of parent ID list failed. Check previous error from logs.")
    elif create_json:
        config.revoke_nothing = True
        revoke_id(config, config.get_parent_id())
    elif revoke_with_json:
        pass
    return


#    # The first run to create full_json
#    if config.get_create_json_bool():
#        revoker.create_full_json()
#    elif config.get_revoke_with_root_id_bool():
#        revoker.create_parent_dict()
#    else:
#        revoker.full_json = revoker.open_json(config.get_full_json_path())
#    
#    if revoker.full_json_creation_error == True:
#        logging.error("Something went wrong with retrieving Google Drive" \
#                + " file structure.")
#        return
#
#    logging.info("### Get files to be revoked")
#    
#    if revoker.conf.get_revoke_with_json_bool():
#        revoker.all_revoke_share_ids_dict = revoker.open_json(config.get_revoke_json_path())
#    # This is now just for preventing unnecessary calculating
#    elif revoker.conf.get_revoke_with_root_id_bool():
#        print(revoker.parent_id_dict)
#        
#        # Create copy and delete root_id.
#        tmp_parent_dict = copy.deepcopy(self.parent_id_dict)
#        tmp_parent_dict.pop(self.conf.get_root_id(), None)
#
#    else:
#        # Go through full_json and create a dict of possible permissions to revoke.
#        # create_all_revoke_share_ids is recursive function.
#        revoker.create_all_revoke_share_ids(revoker.full_json)
#        revoker.write_json_dump(revoker.all_revoke_share_ids_dict, "revoke_all_" \
#            + revoker.conf.get_parent_id())
#    # -1 because the dict has 1 item when the dict is initialized.
#    logging.info("Amount of possible permissions to be revoked: " + \
#            str(len(revoker.all_revoke_share_ids_dict)-1))
#    
#    if len(revoker.all_revoke_share_ids_dict) > 1: 
#        revoker.is_there_something_to_revoke = True
# 
#    # Don't try to revoke if there's nothing to revoke.
#    if revoker.is_there_something_to_revoke:
#        revoker.log_files_to_be_revoked()
#        
#        # Revoke permissions if they're set to be revoked.
#        if revoker.conf.get_revoke_deleted_bool():
#            revoker.revoke_deleted()
#        if revoker.conf.get_revoke_email_domains_bool():
#            revoker.revoke_email_domain_list()
#        if revoker.conf.get_revoke_permissions_bool():
#            revoker.revoke_permission_list()
#        if revoker.conf.get_revoke_current_user_bool():
#            revoker.revoke_current_user()
#        if revoker.conf.get_revoke_emails_bool():
#            revoker.revoke_email_list()
#
#        if revoker.conf.get_revoke_all_except_current_user_bool():
#            revoker.revoke_all_except_current_user()
#
#    # Print the path to new JSON file on the screen.
#    # This should be one of the last things to print as it's needed to configure
#    # configuration file.
#    if config.get_create_json_bool():
#        logging.info("The newly created full JSON: " + revoker.created_full_json_path)
#
#    logging.info("Number of revoke erros: " + str(revoker.num_of_revoke_errors))
#    logging.info("Number of revoked permissions: " + str(revoker.num_of_revoked_permissions))

def revoke_parent_ids(revoker: PermissionRevoker = None):
    """This function goes through parent_ids and revokes permissions defined in
    configuration file.
    """
    return

def revoke_id(conf: ConfParser = None, parent_id: str = None):
    """This function revokes permissions of the parent_id and it's children."""

    # Check args
    if not conf or not isinstance(conf, ConfParser):
        logging.error("Func: {}, no conf given.".format(inspect.stack()[0][3]))
        return
    if not parent_id or not isinstance(parent_id, str):
        logging.error("Func: {}, no parent_id given.".format(inspect.stack()[0][3]))
        return
    
    logging.info("### BEGIN logging revocation of parent ID: " + parent_id)

    tmp_revoker = PermissionRevoker(conf)
    tmp_revoker.create_full_json(parent_id)
    
    if tmp_revoker.full_json_creation_error == True:
        logging.error("Something went wrong with retrieving Google Drive" \
                + " file structure.")
        return
    
    logging.info("### Get files to be revoked")
    
    # Revoke with a previously created JSON if determined in configuration
    # file and not revoking with root_id.
    if conf.get_revoke_with_json_bool() and not conf.get_revoke_with_root_id_bool:
        tmp_revoker.all_revoke_share_ids_dict = tmp_revoker.open_json(conf.get_revoke_json_path())
    else:
        # Go through full_json and create a dict of permissions possible to be revoked.
        # create_all_revoke_share_ids is recursive function.
        tmp_revoker.create_all_revoke_share_ids(tmp_revoker.full_json)
        tmp_revoker.write_json_dump(tmp_revoker.all_revoke_share_ids_dict, "possible_to_revoke" \
            + tmp_revoker.conf.get_parent_id())
    # -1 because the dict has 1 item when the dict is initialized.
    logging.info("Amount of possible permissions to be revoked: " + \
            str(len(tmp_revoker.all_revoke_share_ids_dict)-1))
    
    if len(tmp_revoker.all_revoke_share_ids_dict) > 1: 
        tmp_revoker.is_there_something_to_revoke = True
        tmp_revoker.log_files_to_be_revoked()
    
    # Don't try to revoke if there's nothing to revoke.
    if tmp_revoker.is_there_something_to_revoke and not conf.get_revoke_nothing_bool():
        
        # Revoke permissions if they're set to be revoked.
        if conf.get_revoke_deleted_bool():
            tmp_revoker.revoke_deleted()
        if conf.get_revoke_email_domains_bool():
            tmp_revoker.revoke_email_domain_list()
        if conf.get_revoke_permissions_bool():
            tmp_revoker.revoke_permission_list()
        if conf.get_revoke_current_user_bool():
            tmp_revoker.revoke_current_user()
        if conf.get_revoke_emails_bool():
            tmp_revoker.revoke_email_list()
        if conf.get_revoke_all_except_current_user_bool():
            tmp_revoker.revoke_all_except_current_user()
    
    # Print the path to new JSON file on the screen.
    # This should be one of the last things to print as it's needed to configure
    # configuration file.
    logging.info("The newly created full JSON: " + tmp_revoker.created_full_json_path)
    
    logging.info("Number of revoke erros: " + str(tmp_revoker.num_of_revoke_errors))
    logging.info("Number of revoked permissions: " + str(tmp_revoker.num_of_revoked_permissions))
        
    logging.info("### END logging revocation of parent ID: " + parent_id)

# Example:
# https://realpython.com/python-logging/
def log_to_file(config: ConfParser = None, log_id: str = None):
    log_path = config.get_log_path()
    log_name = log_path + log_id + "_unshare_gdrive_" + \
            datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    
    # Probably some import initializes the logging already,
    # but logging needs to be initialized this way to get the
    # output to certain file.
    # https://stackoverflow.com/a/46098711
    logging.root.handlers = []
    logging.basicConfig(level=config.get_logging_level(), \
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_name),
                logging.StreamHandler()
            ]
    )
if __name__ == '__main__':
    main()
