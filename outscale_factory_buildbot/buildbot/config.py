"""
Read json config files.
"""

import json
import logging
import os.path


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
    logging.info('Fetching repository list from {}'
                 .format(repo_config_path))
    if not os.path.exists(repo_config_path):
        return []

    with open(repo_config_path) as file_handle:
        return json.load(file_handle)
