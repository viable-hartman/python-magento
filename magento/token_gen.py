#!/usr/bin/env python
# coding: utf-8

# Create consumer key & secret in your Magento Admin interface
#
# Short Magento setup explanation:
# 1. Magento Admin > System > Web Services > REST - OAuth Consumers:
#    Add a new consumer for this script.
#    (This creates the consumer_key and consumer_secret token for you)
# 2. Possibly enable rewriting rules for the /api url in the Magento .htaccess
# 3. Magento Admin > System > Web Services > REST - Roles:
#    Give the Customer account some access to stuff (using the customer authorize_url below)
#    or create an Admin account for write access (using the admin authorize_url below)
#    Give the Guest account some access for some basic functionality testing without authorization.
# 4. Magento Admin > System > Web Services > REST - Attributes:
#    Configure ACL attributes access for the role/account configured in 3rd
# -  The customer must have a (frontend) account to login to and authorize the script.
# -  For any created Admin roles in 3rd, the role needs to be mapped to an admin user:
# 5. Magento Admin > System > Permissions > Users:
#    Edit an admin user and under 'REST Role', tick the created Admin REST Role to map it to that account.
#    This admin will get the authorize_url to authorize your script access in the browser.

import json
from os import path
from requests_oauthlib import OAuth1Session
from pprint import pprint

MAGENTO_HOST = 'https://hydrobuilder.com'
MAGENTO_API_BASE = '%s/api/rest/' % MAGENTO_HOST
# Get client_key, and client_secret from: Magento Admin > System > Web Services > REST - OAuth Consumers
TOKFILE = 'tokens.json'

# Endpoint URLs
callback_uri = 'https://127.0.0.1/callback'
# Endpoints found in the OAuth provider API documentation
request_token_url = '{0}/oauth/initiate'.format(MAGENTO_HOST)
# Customer Auth URL (If you're doing Customer API Access)
# authorization_url = '{0}/oauth/authorize'.format(MAGENTO_HOST)
# Admin Auth URL (If you're doing Admin CLI type API Access)
authorization_url = '{0}/hbc/oauth_authorize'.format(MAGENTO_HOST)
access_token_url = '{0}/oauth/token'.format(MAGENTO_HOST)

# Step 1: Get the consumer key and secret if not already stored.
if not path.exists(TOKFILE):
    # You must set this up as described above in Magento 1.9 / OpenMage
    client_key = input('Please enter your consumer key: ')
    client_secret = input('Please enter your consumer secret: ')
    tokens = {
        "client": {
            "client_key": client_key,
            "client_secret": client_secret
        }
    }
else:
    with open(TOKFILE) as tokfile:
        tokens = json.load(tokfile)

# Step 2: Get the access token if not already stored.
if 'access' not in tokens:  # We need an access token.
    oauth_session = OAuth1Session(
            tokens['client']['client_key'],
            client_secret=tokens['client']['client_secret'],
            callback_uri=callback_uri)
    
    # Step 2:a, fetch the request token.
    req_token = oauth_session.fetch_request_token(request_token_url)
    # pprint(req_token)
    
    # Step 2:b. Follow this link and authorize
    auth_follow_url = oauth_session.authorization_url(authorization_url)
    print('Use the following link to authorize this client:')
    print(auth_follow_url)
    
    # Step 2:c. Fetch the access token
    redirect_response = input('Paste entire callback/redirect URL and query parameters: ')
    auth_resp = oauth_session.parse_authorization_response(redirect_response)
    # pprint(auth_resp)
    access_token = oauth_session.fetch_access_token(access_token_url)
    # pprint(access_token)

    # Save the auth_resp, access_token, and existing client settings back to TOKFILE
    tokdata = {
            'client': tokens['client'],
            'verify': auth_resp,
            'access': access_token
    }
    pprint(tokdata)
    with open(TOKFILE, 'w') as outfile:
        json.dump(tokdata, outfile)

else:  # We already have an access_token, so let's test a session
    oauth_session = OAuth1Session(
            tokens['client']['client_key'],
            client_secret=tokens['client']['client_secret'],
            resource_owner_key=tokens['access']['oauth_token'],
            resource_owner_secret=tokens['access']['oauth_token_secret'])

# Done. We can now make OAuth requests to Magento 1.9's / OpenMage's REST API
products_url = '{0}/api/rest/products'.format(MAGENTO_HOST)
r = oauth_session.get(products_url)
if r.status_code == 200:
    pretty_json = json.loads(r.text)
    print(json.dumps(pretty_json, indent=4))
else:
    print(r.text)
print(r.status_code)

# Post Example
# new_price = {'price':  '16.99'}
# oauth_session.post(product_url, data=new_price)
