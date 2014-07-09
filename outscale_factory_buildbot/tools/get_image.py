#!/usr/bin/env python
"""
Tool used to find a single image by name.
"""
from outscale_factory_buildbot.tools.find_images import find_images


class ImageNotFound(Exception):

    """
    Error raised when the image is not found.
    """


def get_image_id(region, pattern='', tags={}):
    """
    Return first image id found.
    """
    images = find_images(region, pattern, tags)
    if not images:
        raise ImageNotFound('No such image region={} pattern={} tags={}'
                            .format(repr(region), repr(pattern), repr(tags)))
    return images[0].id


def main():
    """
    Main function.
    """
    import json
    import sys
    if len(sys.argv) != 4:
        sys.stderr.write('Usage: {} REGION NAME_PATTERN TAGS_JSON\n'
                         .format(sys.argv[0]))
        sys.exit(1)
    try:
        image_id = get_image_id(
            sys.argv[1],
            sys.argv[2],
            json.loads(sys.argv[3]))
    except Exception as error:
        sys.stderr.write('{}\n'.format(repr(error)))
    else:
        sys.stdout.write('IMAGE_ID={}\n'.format(image_id))

if __name__ == '__main__':
    main()
