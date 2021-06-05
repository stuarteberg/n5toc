import os
import re
import logging
from itertools import chain

logger = logging.getLogger(__name__)

def find_files(root_dir, file_exts=None, skip_exprs=None, file_exprs=None):
    """
    Utility for finding files that match a pattern within a directory tree,
    but skipping directories that match a particular pattern.
    Skipped directories are not even searched, saving time.

    Args:
        root_dir:
            The root directory for the search

        file_exts:
            A file extension or list of extensions to search for.
            Cannot be used in conjunction with file_exprs.

        skip_exprs:
            A regular expression (or list of them) to specify which
            directories should be skipped entirely during the search.

            Note:
                The root_dir is always searched, even it if matches
                something in skip_exprs.

        file_exprs:
            A regular expression (or list of them) to specify which file names to search for.
            Cannot be used in conjunction with file_exts.

    Returns:
        list of matching file paths

    Note:
        Only files are searched for. Directories will not be returned,
        even if their names happen to match one of the given file_exprs.

    Example:
        Search for all .json files in an N5 directory hierarchy,
        but skip the block directories such as 's0', 's1', etc.
        Also, skip the 'v1' directories, just for the sake of this example.

        ..code-block:: ipython

            In [1]: root_dir = '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32'
               ...: find_files( root_dir, '.json', ['s[0-9]+', 'v1'])
            Out[1]:
            ['/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/attributes.json',
             '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/v2_acquire_trimmed_sp1_adaptive___20210315_093643/attributes.json',
             '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/v2_acquire_trimmed_sp1_adaptive___20210409_161756/attributes.json',
             '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/v2_acquire_trimmed_sp1_adaptive___20210409_162015/attributes.json',
             '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/v2_acquire_trimmed_sp1_adaptive___20210409_165800/attributes.json',
             '/nrs/flyem/render/n5/Z0720_07m_BR/render/Sec32/v3_acquire_trimmed_sp1_adaptive___20210419_204640/attributes.json']
    """
    assert not file_exts or not file_exprs, \
        "Please specify file extensions or whole file patterns, not both."

    file_exts = file_exts or []
    skip_exprs = skip_exprs or []
    file_exprs = file_exprs or []

    if isinstance(skip_exprs, str):
        skip_exprs = [skip_exprs]
    if isinstance(file_exts, str):
        file_exts = [file_exts]
    if isinstance(file_exprs, str):
        file_exprs = [file_exprs]

    if file_exts:
        # Strip leading '.'
        file_exts = map(lambda e: e[1:] if e.startswith('.') else e, file_exts)

        # Handle double-extensions like '.tar.gz' properly
        file_exts = map(lambda e: e.replace('.', '\\.'), file_exts)

        # Convert file extensions -> file expressions (regex)
        file_exprs = map(lambda e: f".*\\.{e}", file_exts)

    # Combine and compile expression lists
    file_expr = '|'.join(f"({e})" for e in file_exprs)
    file_rgx = re.compile(file_expr)

    skip_expr = '|'.join(f"({e})" for e in skip_exprs)
    skip_rgx = re.compile(skip_expr)

    def _find_files(parent_dir):
        logger.debug("Searching " + parent_dir)

        try:
            # Get only the parent directory contents (not subdir contents),
            # i.e. just one iteration of os.walk()
            _, subdirs, files = next(os.walk(parent_dir))
        except StopIteration:
            return []

        # Matching files
        if file_expr:
            files = filter(lambda f: file_rgx.fullmatch(f), files)
        files = map(lambda f: f"{parent_dir}/{f}", files)

        # Exclude skipped directories
        if skip_expr:
            subdirs = filter(lambda d: not skip_rgx.fullmatch(d), subdirs)
        subdirs = map(lambda d: f"{parent_dir}/{d}", subdirs)

        # Recurse
        subdir_filesets = map(_find_files, subdirs)

        # Concatenate
        return chain(files, *subdir_filesets)

    return list(_find_files(root_dir))
