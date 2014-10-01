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
    if 'marketplace' in factory_config:
        logging.info('Fetching repository list from the Marketplace')
        config = factory_config['marketplace']
        baseurl = config['baseurl']
        username = config['username']
        password = config['password']
        return _get_repo_config_from_marketplace(baseurl,
                                                 username,
                                                 password,
                                                 repo_config_path)
    else:
        logging.info('Fetching repository list from {}'
                     .format(repo_config_path))
        return _read_repo_config_file(repo_config_path)


def _get_repo_config_from_marketplace(baseurl, username, password,
                                      repo_config_path):
    mpclient = MarketplaceClient(baseurl, username, password)
    try:
        appliances = mpclient.get_appliance_list()
    except Exception as exc:
        logging.warning(
            'Failed to fetch appliance list from the Marketplace. Error: {}'
            .format(exc))
        logging.warning('Falling back to local repository list.')
        repos = _read_repo_config_file(repo_config_path)
        if not repos:
            logging.error('No cached repository list found.')
        return repos

    # Create a list at the expected format from the appliance list
    repos = [(each['name'], each['repository'], each['branch'])
             for each in appliances]
    logging.info('Fetched definition of {} repositories from the Marketplace'
                 .format(len(repos)))

    # Store the list
    try:
        with open(repo_config_path, 'w') as file_handle:
            json.dump(repos, file_handle, indent=2)
    except Exception as exc:
        logging.warning('Failed to store list of repositories in {}. Error: {}'
                        .format(repo_config_path, exc))

    return repos


def _read_repo_config_file(repo_config_path):
    if not os.path.exists(repo_config_path):
        return []

    with open(repo_config_path) as file_handle:
        return json.load(file_handle)
