import logging
import multiprocessing
import os
import time
import uuid

import dill
from tinydb import where

from bnb.common import States, goc_db, goc_storage_path, create_all

logger = logging.getLogger(__name__)


class DefaultCtx:

    def __init__(self, *args, **kwargs):
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}'

    @property
    def storage(self):
        return os.getcwd()

    def report(self, key, value, cmp=None):
        print(f'REPORT: key={key}, value={value}')

    def open(self, *args, **kwargs):
        return open(*args, **kwargs)

    def touch(self, file, *args, **kwargs):
        with open(file=file, mode='a+'):
            pass

    def makedirs(self, *args, **kwargs):
        os.makedirs(*args, **kwargs)

    def log_scalar(self, tag, value, step):
        print(f'SCALAR: tag={tag}  value={value:.4f}  step={step}')

    def run(self, f, args, kwargs):
        return f(*args, **kwargs)


class RemoteContext(DefaultCtx):

    def __init__(self, db_entry, upstream_update):

        self._logger = logging.getLogger(self.__class__.__name__ + '@' + db_entry['ID'][:5])

        self._db_entry        = db_entry
        self._ID              = db_entry['ID']
        self._experiment_name = db_entry['rich_id']['name']  # TODO(elan): this...

        create_all(self._ID, self._experiment_name)

        self._storage         = goc_storage_path(self._ID, self._experiment_name)
        self._upstream_update = upstream_update  # TODO(elan): this should be async as in full-bnb
        self._report_cache    = {}

        self._logger.debug(f'Created {self}')

    def __repr__(self):
        return f'{self.__class__.__name__}(ID={self._ID}, storage={self._storage})'

    def _update_upstream(self, *path, value, mode):
        
        self._logger.debug(f'Trying to update upstream (path={path} value={value})')

        if self._upstream_update is None:
            self._logger.debug('Manager was None')
            return

        try:
            self._upstream_update(self._ID, *path, value=dill.dumps(value), mode=mode)
            self._logger.debug('Sent data to manager')

        except EOFError:
            self._logger.warning('Upstream fucked up')
            self._upstream_update = None

    def _update(self, *path, value, mode='replace'):

        self._logger.debug(f'Trying to update all (path={path} value={value})')
        self._update_upstream(*path, value=value, mode=mode)

    @property
    def storage(self):
        return self._storage

    def report(self, key, value, cmp=None):

        self._logger.debug(f'Reporting => ({key}={value})')

        if (cmp is not None) and (key in self._report_cache):

            cached = self._report_cache[key]
            candidate = cmp(cached, value)

            if candidate == cached:
                return

            value = candidate

        path  = ('results', key)

        self._report_cache[key] = value
        self._update(*path, value=value)

    def open(self, file, mode='r', tags=(), description='', **kwargs):
        
        self.touch(file=file, tags=tags, description=description)
        f = open(file=file, mode=mode, **kwargs)

        return f

    def touch(self, file, tags=(), description=''):

        with open(file=file, mode='a+') as f:
            pass

        path  = ['storage', 'files', file]
        value = dict(type='file', tags=tags, description=description)

        self._update(*path, value=value)

    def makedirs(self, name, mode=511, exist_ok=False, tags=(), description=''):

        os.makedirs(name, mode=mode, exist_ok=exist_ok)

        path = ('storage', 'files', name)
        value = dict(type='directory', tags=tags, description=description)

        self._update(*path, value=value)

    def log_scalar(self, tag, value, step):

        self._update('logs', tag, value=(step, value), mode='append')

    def run(self, f, args, kwargs):

        self._logger.info(f"Trying to run f for args={args} kwargs={kwargs}")

        set_current_context(self)

        self._update('status', value=States.RUNNING)

        status = States.UNK
        t0 = time.time()
        self._update('timing', value={'start': t0, 'stop': 0.0})

        try:
            ret = f(*args, **kwargs)
            status = States.OK

        except KeyboardInterrupt:
            ret = None
            status = States.SIGINT

        except Exception as e:
            ret = e
            status = States.FAIL
            self._update('misc', 'error', value=str(e)) 

        finally:
            set_current_context(None)
            t1 = time.time()

            self._update('timing', value={'start': t0, 'stop': t1})
            self._update('status', value=status)

        return ret


class _Context:
    ctx = DefaultCtx()


def set_current_context(ctx):
    if ctx is None:
        ctx = DefaultCtx()

    logger.debug(f'Setting context: {ctx}')
    _Context.ctx = ctx


def get_current_context():
    logger.debug(f'Returning context: {_Context.ctx}')
    return _Context.ctx
