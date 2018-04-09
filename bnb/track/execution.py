import logging
import multiprocessing
import os
import time
import uuid

import dill
from tinydb import where

from bnb.common import (States, goc_db, goc_storage_path, create_all)
from bnb.track.context import (RemoteContext, set_current_context)
from bnb.track.utils import (capture_config, nested_update)

TO_SKIP = {'OK'}


class ExecutionManager:

    def __init__(self, to_skip=TO_SKIP):

        self._logger = logging.getLogger(self.__class__.__name__)

        self._db_lock = multiprocessing.Lock()
        self._skip    = to_skip

        self._logger.debug(f"Created: {self}")

    def _get_initial_entry(self, ID, rich_id, config):

        self._logger.debug(f'returning entry for (ID={ID}, rich_id={rich_id}')

        name  = rich_id['name']
        entry = {
            'ID'         : ID,
            'rich_id'    : rich_id,
            'status'     : States.PRE_DISPATCH,
            'results'    : {},
            'config'     : config,
            'logs'       : {},
            'storage'    : {
                'root'  : goc_storage_path(ID, name),
                'files' : {}
            },  
            'timing' : {
                'start' : 0,
                'stop'  : 0,
            },
            'misc': {
                'command' : '',
                'host'    : {},
                'error'   : ''
            }
        }

        return entry

    def _should_skip(self, name, config):

        def test_func(doc):
            return (doc['config'] == config) & (doc['status'] in self._skip)

        with self._db_lock:
            cond = goc_db(name=name).contains(test_func)

        return cond

    def _insert(self, entry):

        ID = entry['ID']
        self._logger.debug(f'Insert: (ID={ID})')

        with self._db_lock:
            goc_db(ID).insert(entry)

    def _dispatch(self, db_entry, f, args, kwargs):

        self._logger.debug(f'Dispatching: {(f, args, kwargs)}')

        ctx = RemoteContext(db_entry=db_entry, upstream_update=self.update)

        try:
            ret = ctx.run(f, args, kwargs)

        except Exception as e:
            ret = e
            self._logger.error(f'Uncaught exception from ExecutionContext.run(...): {e}')

        else:
            self._logger.debug(f'Context returned {ret}')

        return ret

    def run(self, rich_id, f, args, kwargs):

        self._logger.debug(f'Running {rich_id["name"]} for args '
                           f'{args}, {kwargs}')

        ID      = uuid.uuid4().hex
        name    = rich_id['name']
        config  = capture_config(f, args, kwargs)
        skip    = self._should_skip(name, config)

        if skip:
            self._logger.warning(f'Skipping, because this run was already in DB.')
            return

        with self._db_lock:
            try:
                create_all(ID, name)
            except:
                time.sleep(3)  # TOOD(elan)
                create_all(ID, name)

        entry = self._get_initial_entry(ID, rich_id, config)

        self._insert(entry)
        self._dispatch(entry, f, args, kwargs)

    def update(self, ID, *path, value, mode='replace'):

        if isinstance(value, bytes):
            value = dill.loads(value)

        if path[0] == 'status':
            self._logger.info(f'Status: {value}')

        self._logger.debug(f'Update: (ID={ID}, path={path}, value={value}')

        def fn(doc):
            nested_update(doc, *path, value=value, mode=mode)

        with self._db_lock:
            goc_db(ID).update(fn, where('ID') == ID)
