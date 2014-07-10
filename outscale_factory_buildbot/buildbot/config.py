"""
Read json config files.
"""

import json
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


def read_repo_config(config_dir):
    """
    Read Turnkey Linux repository configuration file.

    Return config dictionary.
    """
    file_path = os.path.join(config_dir, 'tklgit.json')
    with open(file_path) as file_handle:
        return json.load(file_handle)
