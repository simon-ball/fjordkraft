import os
import json
import pprint
import logging
import collections
from contextlib import contextmanager

from .exceptions import FjordKraftException


LOCALCONFIG = 'fjordkraft_config.json'
GLOBALCONFIG = '.fjordkraft_config.json'

default = {
    "database.host":"localhost",
    "database.port":5432,
    "database.user": None,
    "database.password": None,
    "database.database": None,
    "database.dialect": None,
    "loglevel": "INFO",
}

validators = collections.defaultdict(lambda: lambda value: True)
validators['database.port'] = lambda a: isinstance(a, int)

logger = logging.getLogger(__name__)
log_levels = {
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'CRITICAL': logging.CRITICAL,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR,
    None:  logging.NOTSET
}

class Config(collections.abc.MutableMapping):

    instance = None

    def __init__(self, *args, **kwargs):
        if not Config.instance:
            Config.instance = Config.__Config(*args, **kwargs)
        else:
            Config.instance._conf.update(dict(*args, **kwargs))

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __getitem__(self, item):
        return self.instance.__getitem__(item)

    def __setitem__(self, item, value):
        self.instance.__setitem__(item, value)

    def __str__(self):
        return pprint.pformat(self.instance._conf, indent=4)

    def __repr__(self):
        return self.__str__()

    def __delitem__(self, key):
        del self.instance._conf[key]

    def __iter__(self):
        return iter(self.instance._conf)

    def __len__(self):
        return len(self.instance._conf)

    def save(self, filename, verbose=False):
        """
        Saves the settings in JSON format to the given file path.
        :param filename: filename of the local JSON settings file.
        :param verbose: report having saved the settings file
        """
        with open(filename, 'w') as fid:
            json.dump(self._conf, fid, indent=4)
        if verbose:
            print('Saved settings in ' + filename)

    def load(self, filename):
        """
        Updates the setting from config file in JSON format.
        :param filename: filename of the local JSON settings file. If None, the local config file is used.
        """
        if filename is None:
            filename = LOCALCONFIG
        with open(filename, 'r') as fid:
            self._conf.update(json.load(fid))

    def save_local(self, verbose=False):
        """
        saves the settings in the local config file
        """
        self.save(LOCALCONFIG, verbose)

    def save_global(self, verbose=False):
        """
        saves the settings in the global config file
        """
        self.save(os.path.expanduser(os.path.join('~', GLOBALCONFIG)), verbose)

    @contextmanager
    def __call__(self, **kwargs):
        """
        The config object can also be used in a with statement to change the state of the configuration
        temporarily. kwargs to the context manager are the keys into config, where '.' is replaced by a
        double underscore '__'. The context manager yields the changed config object.
        Example:
        >>> with config(safemode=False, database__host="localhost") as cfg:
        >>>     # do dangerous stuff here
        """

        try:
            backup = self.instance
            self.instance = Config.__Config(self.instance._conf)
            new = {k.replace('__', '.'): v for k, v in kwargs.items()}
            self.instance._conf.update(new)
            yield self
        except:
            self.instance = backup
            raise
        else:
            self.instance = backup

    class __Config:
        """
        Stores datajoint settings. Behaves like a dictionary, but applies validator functions
        when certain keys are set.
        The default parameters are stored in datajoint.settings.default . If a local config file
        exists, the settings specified in this file override the default settings.
        """

        def __init__(self, *args, **kwargs):
            self._conf = dict(default)
            self._conf.update(dict(*args, **kwargs))  # use the free update to set keys

        def __getitem__(self, key):
            return self._conf[key]

        def __setitem__(self, key, value):
            logger.log(logging.INFO, u"Setting {0:s} to {1:s}".format(str(key), str(value)))
            if validators[key](value):
                self._conf[key] = value
            else:
                raise FjordKraftException(u'Validator for {0:s} did not pass'.format(key))


# Load configuration from file
config = Config()
config_files = (os.path.expanduser(n) for n in (LOCALCONFIG, os.path.join('~', GLOBALCONFIG)))
try:
    config_file = next(n for n in config_files if os.path.exists(n))
except StopIteration:
    pass
else:
    print("Loading config from '{}'".format(config_file))
    config.load(config_file)
