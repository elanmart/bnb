import os
import shutil

from persistqueue import FIFOSQLiteQueue
from tinydb import TinyDB


_ROOT      = '~/.experiments'
_DB_NAME   = 'db.json'
_META_TAB  = 'meta'
_RUNS_TAB  = 'runs'
_STORAGE   = 'storage'
_QUEUE     = 'queue.pq'
_ENTRY     = 'entry.json'


class States:
    OK            = 'OK'
    UNK           = 'UNK'
    FAIL          = 'FAIL'
    DEAD          = 'DEAD'
    SIGINT        = 'SIGINT'
    RUNNING       = 'RUNNING'
    PRE_DISPATCH  = 'PRE_DISPATCH'


class Tables:
    RUNS = _RUNS_TAB
    META = _META_TAB


_DBS_CACHE = {} 
_ID_2_NAME = {}


def get_root():

    return os.path.expanduser(_ROOT)


def backup_entry_path(ID):

    return os.path.join(goc_storage_path(ID), _ENTRY)


def _check_name(ID, name):

    if (ID is not None) and (ID not in _ID_2_NAME):
        assert name is not None
        _ID_2_NAME[ID] = name

    name = _ID_2_NAME.get(ID, name)

    return name


def create_all(ID, name):
    
    _ID_2_NAME[ID] = name
    
    _ = goc_storage_path(ID, name)
    _ = goc_db(ID, name)
    _ = goc_queue()


def goc_queue(name='default'):

    qname = os.path.expanduser(os.path.join(_ROOT, f'{name}-{_QUEUE}'))
    os.makedirs(os.path.dirname(qname), mode=0o775, exist_ok=True)

    return FIFOSQLiteQueue(path=qname)


def goc_storage_path(ID, name=None):
    
    name = _check_name(ID, name)

    retval = os.path.join(_ROOT, name, ID, _STORAGE)
    retval = os.path.expanduser(retval)
    os.makedirs(retval, mode=0o775, exist_ok=True)

    return retval


def goc_db(ID=None, name=None, table=Tables.RUNS):

    name = _check_name(ID, name)
    db   = _DBS_CACHE.get(name)

    if db is None:

        db_path = os.path.expanduser(os.path.join(_ROOT, name, _DB_NAME))
        dirname = os.path.dirname(db_path) 
        
        os.makedirs(dirname, mode=0o775, exist_ok=True)

        db = TinyDB(db_path)
        _DBS_CACHE[name] = db

    tab = db.table(table)

    return tab


def clear_q():

    path = goc_queue().path
    shutil.rmtree(path)
