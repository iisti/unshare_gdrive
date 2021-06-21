#!/usr/bin/env python3

# For removing whitespaces
import re
# For parsing configuration file
from configparser import ConfigParser

# For determining logging level
import logging

class ConfParser:
    """A class for parsing configuration files."""

    def __init__(self):
        self.config = ConfigParser()

    def load_ini_conf(self, conf_file):
        """Loads a configuration file.

        Parameters
        ----------
        config_file : str
            A configuration file in the OS with path.
        """

        self.config.read(conf_file)

    def get_logging_level(self):
        """Returns the log level which should be used for logging.
        logging.LEVEL's type is int."""

        log_level = self.config['Data']['log_level']
        if log_level.lower() == "debug":
            return logging.DEBUG
        elif log_level.lower() == "info":
            return logging.INFO
        elif log_level.lower() == "warning":
            return logging.WARNING
        elif log_level.lower() == "error":
            return logging.ERROR
        elif log_level.lower() == "critical":
            return logging.CRITICAL

    def get_parent_id(self):
        """Returns parent_id which children directories/files should be unshared."""

        return self.config['Data']['parent_id']

    def get_root_id(self):
        """Returns root_id which children directories/files should be unshared.
        root_id is used for creating a list of parent_ids."""

        return self.config['Data']['root_id']

    def get_revoke_permission_list(self):
        """Returns list of permission IDs to revoke from shares."""

        # Remove whitespaces and create list of the config file property
        # Source: https://stackoverflow.com/a/3739928/3498768
        # Do not convert to lower case as it will mess up comparison.
        tmp_str = re.sub(r'\s+', '', self.config['Data']['revoke_permission_list'])
        tmp_list = tmp_str.split(",")
        
        return tmp_list
    
    def get_revoke_email_domain_list(self):
        """Returns list of email domains to revoke."""

        # Remove whitespaces and create list of the config file property
        # Source: https://stackoverflow.com/a/3739928/3498768
        tmp_str = re.sub(r'\s+', '', self.config['Data']['revoke_email_domain_list'].lower())
        tmp_list = tmp_str.split(",")
        
        return tmp_list

    def get_revoke_email_list(self):
        """Returns list of email addresses to revoke from shares."""

        # Remove whitespaces and create list of the config file property
        # Source: https://stackoverflow.com/a/3739928/3498768
        tmp_str = re.sub(r'\s+', '', self.config['Data']['revoke_email_list'].lower())
        tmp_list = tmp_str.split(",")
        
        return tmp_list

    def get_revoke_json_path(self):
        """Returns a path to JSON file which contains all files/folders/permissions which could be
        revoked by current user."""

        return self.config['Data']['revoke_json_path']

    def get_full_json_path(self):
        """Returns a path to JSON file which is created on first run of unshare_gdrive.py"""

        return self.config['Data']['full_json']
    
    def get_output_path(self):
        """Returns JSON output path."""

        return self.config['Data']['output_path']
    
    def get_log_path(self):
        """Returns
        -------
        str
            log output path.
        """
        
        return self.config['Data']['log_path']

    def get_wait_between_batch_calls(self):
        """Retrieves a number of seconds to wait between batch calls.
        Returns
        -------
        int
            A value how long the program should sleep between batch calls in second.
        """

        return int(self.config['Data']['wait_between_batch_calls'])
    
    def get_create_json_bool(self):
        """Returns boolean value True if creation of JSON is enabled in conf
        file.
        
        Returns
        -------
        bool
            Determines if creation of JSON file should be done.
        """

        if self.config['Data']['create_json'].lower() == "true":
            return True
        else:
            return False

    def get_revoke_nothing_bool(self):
        """Returns boolean value Ture if nothing should be revoked."""
        if self.config['Data']['revoke_nothing'].lower() == "true":
            return True
        else:
            return False

    def get_revoke_with_root_id_bool(self):
        """Returns boolean value True if root_id should be used for creating a parent_id list for
        revocation."""
        
        if self.config['Data']['revoke_with_root_id'].lower() == "true":
            return True
        else:
            return False

    def get_revoke_deleted_bool(self):
        """Returns boolean value True if users who are marked as deleted, but permissions
        are left behind, should be revoked."""

        if self.config['Data']['revoke_deleted'].lower() == "true":
            return True
        else:
            return False
    
    def get_revoke_emails_bool(self):
        """Returns boolean value True if users with certain email addresses should be revoked of
        their permissions."""

        if self.config['Data']['revoke_emails'].lower() == "true":
            return True
        else:
            return False
    
    def get_revoke_permissions_bool(self):
        """Returns boolean value True if permissions defined in configuration file should be revoked of
        their permissions."""

        if self.config['Data']['revoke_permissions'].lower() == "true":
            return True
        else:
            return False
    
    def get_revoke_email_domains_bool(self):
        """Returns boolean value True if email domains defined in configuration file should be revoked of
        their permissions."""

        if self.config['Data']['revoke_email_domains'].lower() == "true":
            return True
        else:
            return False
    
    def get_revoke_current_user_bool(self):
        """Returns boolean value True if current user should be revoked. This doesn't revoke files
        that are owned by the current user."""

        if self.config['Data']['revoke_current_user'].lower() == "true":
            return True
        else:
            return False
    
    def get_revoke_all_except_current_user_bool(self):
        """Returns boolean value True if every permission except current user should be revoked.
        Notice that current user can't revoke permissions from files that the current user is not
        either editor with sharing cababilty or owner."""

        if self.config['Data']['revoke_all_except_current_user'].lower() == "true":
            return True
        else:
            return False

    def get_revoke_with_json_bool(self):
        """Returns boolean value True if previously created JSON file should be as a basis of
        revocation information."""

        if self.config['Data']['revoke_with_json'].lower() == "true":
            return True
        else:
            return False

    def get_conf_str(self):
        """Returns all data that was parsed from configuration file as
        a string."""

        # Temp variable for storing multiline string of configuration
        # parameters.
        tmp_conf = ""

        for each_section in self.config.sections():
            for (key, val) in self.config.items(each_section):
                # Create newline if something has been added already.
                if tmp_conf:
                    tmp_conf += "\n"
                if key == "full_json" and self.get_create_json_bool():
                    tmp_conf += "WARNING: full_json in conf file will be " \
                            + "ignored as a new one will be created.\n"
                tmp_conf += key + " = " + val
        
        return tmp_conf

    def print_conf(self):
        """Prints all data that was parsed from configuration file."""

        for each_section in self.config.sections():
            for (key, val) in self.config.items(each_section):
                print(key, "=", val)
