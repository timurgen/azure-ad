# azure-ad
[![Build Status](https://travis-ci.org/sesam-community/azure-ad.svg?branch=master)](https://travis-ci.org/sesam-community/azure-ad)

Sesam datasource and sink uses Microsoft Graph to read and write users and groups to Azure AD

### Azure AD access 

To be able to communicate with Azure AD we need to register an applicaiton in Azure AD and obtain client id and client secret needed for Oauth:

Navigate to https://aad.portal.azure.com -> Dashboard -> App Registrations and create new app

You also need to assign required permissions to this app such as `User.ReadWrite.All, Directory.ReadWrite.All, Group.ReadWrite.All`  
read more [here](https://docs.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0&tabs=cs)

This app uses Outh2 authentication with client_credentials. You need to provide next environment variables:

* `client_id` - from registered application
* `client_secret` - from registered application
* `tenant_id` - Tenant id my be found in Azure AD properties 



### System setup 

```json
{
  "_id": "ms-graph-test-service",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "LOG_LEVEL": "DEBUG|INFO|WARNING|ERROR",
      "client_id": "<client id>",
      "client_secret": "<client secret>",
      "tenant_id": "<azure tenant id>"
    },
    "image": "<docker image>",
    "port": 5000
  },
  "verify_ssl": true
}
```

### Setup for "fetch" pipe

```json
{
  "_id": "<pipe id>",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "ms-graph-test-service",
    "url": "/datasets/users/entities"
  }
}

```

### Setup for "create/update" pipe

You need to supply correct representation of user. There are different requirements when you create or update an user.  
For example `passwordProfile` must be supplied to create user but not allowed when you update user.  
Another very important attribute is `userPrincipalName` -  By convention, this should map to the user's email name. The general format is alias@domain, where domain must be present in the tenant’s collection of verified domains.   

Read more [here](https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-beta)

```json
{
  "_id": "<pipe id>",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "<source dataset name>"
  },
  "sink": {
    "type": "json",
    "system": "<sink system id>",
    "url": "/datasets/user"
  },
  "transform": {
    "type": "dtl",
    "rules": {
      "default": [
        ["copy", "*"],
        ["add", "jobTitle", "programmer"]
      ]
    }
  }
}

```
