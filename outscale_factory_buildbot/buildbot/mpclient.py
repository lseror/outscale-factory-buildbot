#!/usr/bin/env python
import json

import requests

GET_APPLIANCE_PATH = '/api/v1/appliances/?limit=0'


class MarketplaceClient(object):
    def __init__(self, baseurl, username, password):
        self.baseurl = baseurl
        self.auth = (username, password)

    def get_appliance_list(self):
        """
        Fetch a list of Turn Key Linux appliances from a Marketplace host
        """
        url = self.baseurl + GET_APPLIANCE_PATH
        headers = {'content-type': 'application/json'}
        response = requests.get(url, auth=self.auth, headers=headers)
        if response.status_code != 200:
            raise Exception(
                'Fetching appliance list failed with HTTP error code {}. {}'
                .format(response.status_code, response.text))

        dct = json.loads(response.text)

        if not 'objects' in dct:
            raise Exception('Missing "objects" item in JSON appliance list')

        return dct['objects']


def main():
    import getpass

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('marketplace_baseurl')
    parser.add_argument('-p', '--password')

    args = parser.parse_args()
    if not args.password:
        args.password = getpass.getpass()

    mpclient = MarketplaceClient(args.marketplace_baseurl,
                                 args.username,
                                 args.password)
    print(mpclient.get_appliance_list())
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
