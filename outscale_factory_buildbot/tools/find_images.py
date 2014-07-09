#!/usr/bin/env python
"""
Tool used to find virtual machine images by name.
"""
from fnmatch import fnmatch
import boto.ec2


def find_images(region, pattern='', tags={}):
    """
    Take name pattern and/or tags,
    return list of image objects,
    sorted by name in reverse order.

    The name pattern is shell style: ?*[seq][!seq].
    """
    conn = boto.ec2.connect_to_region(region)
    filters = {}
    if tags:
        filters.update(('tag' + k, tags[k]) for k in tags)
    images = conn.get_all_images(filters=filters)
    if pattern:
        images = [each for each in images
                  if fnmatch(each.name, pattern)]
    return sorted(
        images,
        reverse=True,
        key=lambda x: x.name)


def main():
    """
    Main function.
    """
    import json
    import pprint
    import sys
    if len(sys.argv) != 4:
        sys.stderr.write('Usage: {} REGION NAME_PATTERN TAGS_JSON\n'
                         .format(sys.argv[0]))
        sys.exit(1)
    images = find_images(
        sys.argv[1],
        sys.argv[2],
        json.loads(sys.argv[3]))
    name_list = [each.name for each in images]
    id_list = [each.id for each in images]
    json.dump(name_list, sys.stderr, indent=4, separators=(',', ': '))
    sys.stderr.write('\n')
    json.dump(id_list, sys.stdout, indent=4, separators=(',', ': '))
    sys.stdout.write('\n')
    
if __name__ == '__main__':
    main()
