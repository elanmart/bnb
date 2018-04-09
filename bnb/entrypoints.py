import os
from argparse import ArgumentParser as ArgParser

from bnb.utils.general_utils import caller_git_info
from bnb.utils.general_utils import normalize_path
from bnb.utils.version import bump_version
from bnb.utils.version import get_version

__all__ = ['bump' , 'print_version']


def _autoarg(name, **kwargs):
    parser = ArgParser()
    parser.add_argument(name, **kwargs)
    arg = getattr(parser.parse_args(), name)

    return arg


def _bump(part):
    fname = normalize_path(os.getcwd())
    git_root, git_hash, _ = caller_git_info(fname)

    bump_version(name=git_root, commit=git_hash, part=part)


def bump():
    part = _autoarg('part', choices={'major', 'minor', 'patch'},
                    help="which part of version should we bump")
    _bump(part)


def v():
    vs = get_version(caller_git_info(os.getcwd()))
    print(f'version:\n{str(vs)}')
