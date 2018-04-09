import inspect
import os
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path
from typing import *

import git


@contextmanager
def chdir(path):
    old = os.getcwd()
    os.chdir(path)
    
    yield

    os.chdir(old)


def normalize_path(path: Union[Path, str]) -> Path:
    if not isinstance(path, Path):
        path = Path(path)

    return path.expanduser().absolute().resolve()


def get_caller_globals():
    return inspect.stack()[1][0].f_back.f_globals


def caller_git_info(filename=None):
    retval = namedtuple('retval', ('root', 'hash', 'dirty'))

    if filename is None:
        previous_frame = inspect.currentframe().f_back.f_back
        filename, *_ = inspect.getframeinfo(previous_frame)

    filename = filename or os.path.dirname(normalize_path(filename))
    filename = str(filename)

    if os.path.basename(filename).startswith('<ipython'):
        filename = os.path.dirname(filename)

    try:
        git_repo = git.Repo(filename, search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")
        git_hash = git_repo.head.commit.hexsha[:7]
        is_dirty = git_repo.is_dirty()

    except git.InvalidGitRepositoryError:
        git_root = filename
        git_hash = None
        is_dirty = False

    return retval(normalize_path(git_root), git_hash, is_dirty)
