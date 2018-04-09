from collections import namedtuple
from typing import Union

from bnb.common import Tables, goc_db

DEFAULT_VERSION = '0.0.0.1'


_Version = namedtuple('Version', ('major', 'minor', 'patch', 'commit'))
class Version(_Version):
    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}.{self.commit}'


def from_string(v: str):
    v = v.split('.')
    v += ['0'] * (4 - len(v))

    assert len(v) == 4
    assert all(item.isdigit() for item in v)

    v = [int(item) for item in v]

    return Version(*v)


def as_version_obj(v: Union[Version, str]) -> Version:
    if isinstance(v, str):
        v = from_string(v)

    assert isinstance(v, Version)

    return v


def _bump(v: Union[Version, str], 
          part: property = Version.commit):

    if not isinstance(part, str):
        inv_dict = {getattr(Version, k): k for k in dir(Version) if (not k.startswith('_'))}
        part = inv_dict[part]

    v = as_version_obj(v)
    i = v._fields.index(part)

    v = list(v)
    v[i] += 1

    for j in range(i + 1, len(v)):
        v[j] = 0

    return Version(*v)


def _get_entry(table, commit='0000000000000000000000000000000000000000'):

    if len(table) == 0:
        entry = dict(last_commit=commit, version=DEFAULT_VERSION)
        table.insert(entry)

    return table.all()[0]

def bump_version(name, commit, part=None) -> Version:

    table       = goc_db(name=name, table=Tables.META)
    entry       = _get_entry(table, commit)
    version     = entry['version']
    last_commit = entry['last_commit']

    if (part is None) and (last_commit != commit):
        part = Version.commit

    if part is None:
        return version

    new_version = _bump(version, part=part)

    table.update({
        'version':     str(new_version),
        'last_commit': commit
    })

    return new_version


def get_version(name, commit=None) -> str:
    return str(bump_version(name=name, commit=commit, part=None))
