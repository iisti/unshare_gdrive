# Development tips

## Default capabilities of different Google File share roles
* https://developers.google.com/drive/api/v3/ref-roles
* API tester:
  * https://developers.google.com/drive/api/v3/reference/files/get

#### Editor default capabilities
~~~
"capabilities": {
  "canAddChildren": true,
  "canAddMyDriveParent": false,
  "canChangeCopyRequiresWriterPermission": false,
  "canChangeViewersCanCopyContent": false,
  "canComment": true,
  "canCopy": false,
  "canDelete": false,
  "canDownload": true,
  "canEdit": true,
  "canListChildren": true,
  "canModifyContent": true,
  "canMoveChildrenWithinDrive": true,
  "canMoveItemIntoTeamDrive": false,
  "canMoveItemOutOfDrive": false,
  "canMoveItemWithinDrive": true,
  "canReadRevisions": false,
  "canRemoveChildren": true,
  "canRemoveMyDriveParent": true,
  "canRename": true,
  "canShare": true,
  "canTrash": false,
  "canUntrash": false
 }
}
~~~ 

#### Commenter default capabilities
~~~
"capabilities": {
  "canAddChildren": false,
  "canAddMyDriveParent": false,
  "canChangeCopyRequiresWriterPermission": false,
  "canChangeViewersCanCopyContent": false,
  "canComment": true,
  "canCopy": false,
  "canDelete": false,
  "canDownload": true,
  "canEdit": false,
  "canListChildren": true,
  "canModifyContent": false,
  "canMoveChildrenWithinDrive": false,
  "canMoveItemIntoTeamDrive": false,
  "canMoveItemOutOfDrive": false,
  "canMoveItemWithinDrive": false,
  "canReadRevisions": false,
  "canRemoveChildren": false,
  "canRemoveMyDriveParent": true,
  "canRename": false,
  "canShare": false,
  "canTrash": false,
  "canUntrash": false
 }
}
~~~

#### Viewer default capabilities
~~~
"capabilities": {
  "canAddChildren": false,
  "canAddMyDriveParent": false,
  "canChangeCopyRequiresWriterPermission": false,
  "canChangeViewersCanCopyContent": false,
  "canComment": false,
  "canCopy": false,
  "canDelete": false,
  "canDownload": true,
  "canEdit": false,
  "canListChildren": true,
  "canModifyContent": false,
  "canMoveChildrenWithinDrive": false,
  "canMoveItemIntoTeamDrive": false,
  "canMoveItemOutOfDrive": false,
  "canMoveItemWithinDrive": false,
  "canReadRevisions": false,
  "canRemoveChildren": false,
  "canRemoveMyDriveParent": true,
  "canRename": false,
  "canShare": false,
  "canTrash": false,
  "canUntrash": false
 }
}
~~~

## Create chunks of batch calls
* Chunkign example https://stackoverflow.com/a/312464/3498768
* There is error if a batch exceeds maximum amount of calls
~~~
googleapiclient.errors.BatchError: <BatchError "Exceeded the maximum calls(1000) in a single batch request.">
~~~

## Check Quota limits
* Quota limits: https://console.developers.google.com/apis/api/drive.googleapis.com/quotas?project=unshare-gdrive-v-1585055155189
* Error after quota has been gone over.
~~~
2021-01-10 21:58:23,696 - ERROR -     Error revoking: <HttpError 403 when requesting https://www.googleapis.com/drive/v3/files/0B_yh_IM0HMnVNDlscHVaeWNpWTA/permissions/08713607137449058341? returned "Rate Limit Exceeded". Details: "Rate Limit Exceeded">
~~~

## Http exception errors
* "Permission not found"
~~~
2021-01-15 07:54:02,311 - ERROR -     Error revoking: <HttpError 404 when requesting
https://www.googleapis.com/drive/v3/files/1fmTENgYP9Nb_PqreKEUg2YhSnbUGbA3j/permissions/08713607137449058341?
returned "Permission not found: 08713607137449058341.". Details: "Permission not found:
08713607137449058341.">
~~~
* "File not found"
~~~
2021-01-18 22:32:44,651 - ERROR - File not found: 0B7QenxLrjDzGMGRZYlJya0NOeFk.
~~~

## Special permission IDs
* If a folder/file is shared widely, the permission ID can be:
  * anyoneWithLink = if one has the URL, one can view
  * anyone = completely public
* Example of anyoneWithLink
~~~
"permissions": [
    {
        "kind": "drive#permission",
        "id": "anyoneWithLink",
        "type": "anyone",
        "role": "reader",
        "allowFileDiscovery": false
    }
]
~~~

## Domain permission vs user permission
* Example of permissions for domain vs user
~~~
"permissions": [
    {
        "kind": "drive#permission",
        "id": "08713607137449011111",
        "type": "domain",
        "domain": "example-domain.com",
        "role": "reader",
        "allowFileDiscovery": true,
        "displayName": "Domain Company"
    },
    {
        "kind": "drive#permission",
        "id": "18151941492630421111",
        "type": "user",
        "emailAddress": "user.name@example-domain.com",
        "role": "owner",
        "displayName": "User Name",
        "deleted": false
    }
]
~~~

## Create a link to any folder/file from a hash
* One can create a link by adding the Google folder/file hash/ID in the end of this URL:
  
      https://drive.google.com/open?id=
      
## Inspecting output files
* One can grep unique email addresses from JSON files, sort -u removes duplicates  
    
      grep emailAddress json_file.json | sort -u
      
## Example of a revoke dict
* The empty_dict is there, so that the revoke dict doesn't come empty at any point. 
* There's a domain share.
* There's a deleted user.
* There's a user with email.
* There's a "user" anyone with anyoneWithLink permission.
~~~
{
    "empty_dict": {
        "revoke_permissions": {
            "empty_permission": {
                "the_only": "If this is the only one left, all other permissions have been removed."
            }
        }
    },
    "1brCnA1111Vbh0yC6Cqh8Q4S11112mkxJkKWI11Bi08o": {
        "name": "Artikkeli",
        "owner.me": true,
        "revoke_permissions": {
            "00713607137449058007": {
                "domain": "example-domain.com",
                "role": "reader"
            },
            "11113221111597600818": {
                "emailAddress": "",
                "role": "writer",
                "deleted": true
            },
            "anyoneWithLink": {
                "role": "reader"
            }
        }
    },
        "1DoHiv4flfJ7lU11113rgCum1111oP1111Z8WRewFQ8": {
        "name": "Cash Money Geld Raha",
        "owner.me": true,
        "revoke_permissions": {
            "11111028641111386047": {
                "emailAddress": "user.name@example-domain.com",
                "role": "commenter",
                "deleted": false
            }
        }
    }
}
~~~

## Shortcuts don't show share status
* If a file/folder icon has an curved arrow, that means it's a shortcut.
  * Source: https://support.google.com/drive/thread/47533474?hl=en
* Some information about shortcuts
  * Google rolls out Drive shortcuts to simplify folder structure, sharing https://9to5google.com/2020/03/26/google-drive-file-shortcuts/
  * Find files & folders with Google Drive shortcuts https://support.google.com/drive/answer/9700156?co=GENIE.Platform%3DAndroid&hl=en
  * Single-parenting behavior changes https://developers.google.com/drive/api/v3/ref-single-parent
* Shortcut's shared property seems to be always false, even if the targetId/file/folder is shared. Here's shortcut's data:
  ~~~
  {
      "kind": "drive#file",
      "id": "1cXv_Pes_803wBUY0p11111111111111",
      "name": "test-share-folder1",
      "mimeType": "application/vnd.google-apps.shortcut",
      "parents": [
          "1kJnb_S8qi6tq3aoei-11111111111111"
      ],
      "createdTime": "2021-01-23T11:54:26.359Z",
      "modifiedTime": "2021-01-23T11:54:26.359Z",
      "owners": [
          {
              "displayName": "Another User",
              "me": true,
              "permissionId": "18151941491111111111",
              "emailAddress": "anotheruser1@example-domain.com"
          }
      ],
      "shared": false,
      "capabilities": {
          "canShare": false
      },
      "shortcutDetails": {
          "targetId": "1bFA11aAh7AiO7EYiVV11111111111111",
          "targetMimeType": "application/vnd.google-apps.folder"
      }
  }
  ~~~
* Shortcut's targetId's data:
  ~~~
  {
      "kind": "drive#file",
      "id": "1bFA11aAh7AiO7EYiVV11111111111111",
      "name": "test-share-folder1",
      "mimeType": "application/vnd.google-apps.folder",
      "createdTime": "2021-01-23T11:53:30.783Z",
      "modifiedTime": "2021-01-23T11:54:25.751Z",
      "owners": [
          {
              "displayName": "User1 Name1",
              "me": false,
              "permissionId": "05834667591111111111",
              "emailAddress": "user1.name1@example-domain.com"
          }
      ],
      "shared": true,
      "capabilities": {
          "canShare": true
      },
      "permissions": [
          {
              "kind": "drive#permission",
              "id": "18151941491111111111",
              "type": "user",
              "emailAddress": "anotheruser1@example-domain.com",
              "role": "writer",
              "displayName": "Another User",
              "deleted": false
          },
          {
              "kind": "drive#permission",
              "id": "05834667591111111111",
              "type": "user",
              "emailAddress": "user1.name1@example-domain.com",
              "role": "owner",
              "displayName": "User1 Name1",
              "photoLink": "https://lh3.googleusercontent.com/a-/AOh14GjCZ1loEd2H-GJbpYvxSh55tHNLC81111111111=s64",
              "deleted": false
          }
      ],
      "children": []
  }
  ~~~
