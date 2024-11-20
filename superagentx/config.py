import logging
import os
import sys


def is_verbose_enabled():
    verbose = os.environ.get('DEBUGGING') or os.environ.get('VERBOSE')
    if verbose and verbose.lower() in ('1', 'true'):
        logging.basicConfig(
            format='%(name)s - %(levelname)s - %(message)s',
            stream=sys.stdout,
            level=logging.DEBUG,
            force=True
        )
