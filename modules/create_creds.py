#!/usr/bin/env python3

# Defaults in quickstart.py
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For checking object type isinstance(service, Resource)
from googleapiclient.discovery import Resource

# After modifying scopes, delete the file token.pickle, so a new one is generated.
# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
# Scopes https://developers.google.com/identity/protocols/oauth2/scopes#drivev3
# /auth/drive  contains: See, edit, create, and delete all of your Google Drive files
SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveService:
    def __init__(self, service: Resource = None):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        # Added "cache_discovery=False" otherwise there will be error:
        # ImportError: file_cache is unavailable when using oauth2client >= 4.0.0 or google-auth
        # Source: https://github.com/googleapis/google-api-python-client/issues/299
        self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
