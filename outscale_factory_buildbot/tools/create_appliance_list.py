#!/usr/bin/env python
import json

import requests

GET_APPLIANCE_PATH = '/api/v1/appliances/?limit=0'

def get_appliance_list(marketplace_baseurl, username, password):
    """
    Fetch a list of Turn Key Linux appliances from a Marketplace host
    """

    url = marketplace_baseurl + GET_APPLIANCE_PATH
    headers = {'content-type': 'application/json'}
    response = requests.get(url, auth=(username, password), headers=headers)
    if response.status_code != 200:
        raise Exception(
            'Fetching appliance list failed with HTTP error code {}.\n{}'
            .format(response.status_code, response.text))

    dct = json.loads(response.text)

    if not 'objects' in dct:
        raise Exception('Missing "objects" item in JSON appliance list')

    return dct['objects']


def write_appliance_list(lst, fp):
    """
    Take a list of appliances retrieved from the Marketplace and write it using
    the expected structure of tklapp.json
    """
    lst = [(each['name'], each['repository'], each['branch']) for each in lst]
    json.dump(lst, fp, indent=2)


def main():
    import getpass

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('marketplace_baseurl')
    parser.add_argument('-p', '--password')
    parser.add_argument('-o', '--output')

    args = parser.parse_args()
    if not args.password:
        args.password = getpass.getpass()

    if args.output:
        fp = open(args.output, 'w')
    else:
        fp = sys.stdout

    try:
        lst = get_appliance_list(args.marketplace_baseurl,
                                 args.username,
                                 args.password)
    except Exception as exc:
        sys.stderr.write(str(exc) + '\n')
        return 1

    write_appliance_list(lst, fp)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
