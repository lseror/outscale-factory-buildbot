"""
Read json config files.
"""

import json
import logging
import os.path

from mpclient import MarketplaceClient

def read_factory_config(config_dir):
    """
    Read and merge factory config files.

    Return config dictionary.
    """
    config = {}
    for file_name in 'master.json', 'slave.json', 'user.json':
        file_path = os.path.join(config_dir, file_name)
        with open(file_path) as file_handle:
            config.update(json.load(file_handle))
    return config


def read_repo_config(factory_config, repo_config_path):
    """
    Read Turnkey Linux repository configuration file.

    Return config dictionary.
    """
    mpconfig = factory_config['marketplace']
    mpclient = MarketplaceClient(mpconfig['baseurl'],
                                 mpconfig['username'],
                                 mpconfig['password'])
    try:
        appliances = mpclient.get_appliance_list()
    except Exception as exc:
        logging.warning(
            'Failed to fetch appliance list from the Marketplace. Error: {}'
            .format(exc))
        if os.path.exists(repo_config_path):
            logging.warning('Using cached list instead.')
            with open(repo_config_path) as file_handle:
                return json.load(file_handle)
        else:
            logging.error('No cached list of repositories to fallback to. ' +
                          'Returning an empty list.')
            return []

    repos = [(each['name'], each['repository'], each['branch'])
             for each in appliances]

    # Store the list we just fetched
    try:
        with open(repo_config_path, 'w') as file_handle:
            json.dump(repos, file_handle, indent=2)
    except Exception as exc:
        logging.warning('Failed to store list of repositories in {}. Error: {}'
                        .format(repo_config_path, exc))

    return repos
