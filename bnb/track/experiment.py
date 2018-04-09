import logging
import os
from collections import OrderedDict
from contextlib import contextmanager
from enum import Enum

import wrapt

from .execution import ExecutionManager
from bnb.utils.general_utils import caller_git_info
from bnb.utils.version import get_version


class DispatchMode(Enum):
    ENQUEUE = '_enqueue'
    EXECUTE = '_execute'
    CALL    = '_call'


class Experiment:
    def __init__(self, *identifiers,
                 auto_enabled=False,
                 dirty_ok=False,
                 bucket=None):

        self.identifiers = list(OrderedDict.fromkeys(identifiers))
        self._bucket     = bucket

        (self._root,
         self._commit,
         self._dirty) = caller_git_info()

        if self._dirty and dirty_ok is False:
            raise RuntimeError('Experiment commit cannot be dirty')

        if len(self.identifiers) == 0 or self.identifiers[0] is None:
            name = os.path.basename(self._root)
            self.identifiers = [name] + self.identifiers[1:]

        self._name = self.identifiers[0]
        self._dispatch_mode = None if (not auto_enabled) else DispatchMode.EXECUTE

        self._logger = logging.getLogger(f'Experiment@{self._name}')
        self._logger.debug(f'Created {self}')

    def __repr__(self):
        return f'Experiment(name={self._name})'

    def describe(self):
        self._logger.debug(f'Descrbing: [{",".join(self.identifiers)}]')

        return dict(
            name    = self.identifiers[0],
            tags    = self.identifiers[1:],
            version = get_version(self._name, self._commit),
            commit  = self._commit,
            root    = str(self._root),
            bucket  = self._bucket
        )

    @wrapt.decorator
    def watch(self, wrapped, instance, args, kwargs):
        self._logger.debug(f'Now watching: {wrapped}')
        return self._dispatch(wrapped, args, kwargs)

    @contextmanager
    def call(self):
        prev = self._dispatch_mode

        self._dispatch_mode = DispatchMode.CALL
        yield
        self._dispatch_mode = prev

    @contextmanager
    def queued(self, name='default'):
        raise NotImplementedError("Queue is not implemented "
                                  "in the simpified version "
                                  "of bnb")

    @contextmanager
    def execute(self):
        prev = self._dispatch_mode

        self._dispatch_mode = DispatchMode.EXECUTE
        yield
        self._dispatch_mode = prev

    @property
    def _dispatch_map(self):
        return {
            DispatchMode.ENQUEUE: self._enqueue,
            DispatchMode.EXECUTE: self._execute,
            DispatchMode.CALL:    self._call,
        }

    def _dispatch(self, f, args, kwargs):
        assert (self._dispatch_mode is not None), "Distapch mode not configured..."

        self._logger.debug(f'Dispatching for: {self._dispatch_mode}')

        dispatcher = self._dispatch_map[self._dispatch_mode]
        return dispatcher(f, args, kwargs)

    def _enqueue(self, f, args, kwargs):
        raise NotImplementedError("Queueing is not implemented "
                                  "in the simplified version of "
                                  "bnb.")

    def _execute(self, f, args, kwargs):
        em = ExecutionManager()  #TODO(elan)
        em.run(self.describe(), f, args, kwargs)

    def _call(self, f, args, kwargs):
        return f(*args, **kwargs)

    def tag(self, tag):
        if tag not in self.identifiers:
            self.identifiers.append(tag)
