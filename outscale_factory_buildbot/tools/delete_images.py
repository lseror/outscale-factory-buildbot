#!/usr/bin/env python
"""
Tool used to delete images.
"""
import boto.ec2
import sys


def delete_images(region, image_id_list):
    """
    Delete all images and associated snapshots.
    """
    conn = boto.ec2.connect_to_region(region)
    for image_id in image_id_list:
        sys.stderr.write('Deleting {}\n'.format(image_id))
        conn.deregister_image(image_id, delete_snapshot=True)


def main():
    """
    Main function.
    """
    import json
    if len(sys.argv) not in (2, 3):
        sys.stderr.write('Usage: {} REGION AMI_ID_LIST_JSON\n'
                         .format(sys.argv[0]))
        sys.exit(1)
    region = sys.argv[1]
    if sys.argv[2] == '-':
        ami_id_list = json.load(sys.stdin)
    else:
        ami_id_list = json.loads(sys.argv[2])
    delete_images(region, ami_id_list)

if __name__ == '__main__':
    main()
