import collections
import datetime
import json
import os.path
import sys

from ..util.logger import Logger
from .configuration import CONFIG_DIRECTORY

logger = Logger("config.cutoff_history")
logger.setstream("default", sys.stdout, Logger.WARNING)


DEFAULT_CONFIG_FILE = os.path.expanduser(os.path.join(CONFIG_DIRECTORY, "cutoff_history.json"))


class HistoryEntry(collections.namedtuple("HistoryEntry", ["filename", "frame", "time", "radii"])):
    class Date(object):
        def __init__(self, *args, **kwargs):
            if not isinstance(args[0], datetime.datetime):
                self._date = datetime.datetime(*args, **kwargs)
            else:
                datetime_obj = args[0]
                self._date = datetime_obj

        def __str__(self):
            return repr(self)

        def __repr__(self):
            return self._date.strftime("%m/%d/%y, %H:%M")

        def __gt__(self, other):
            return self._date > other._date

        @property
        def datetime_obj(self):
            return self._date

    def __new__(cls, filename, frame, time, radii):
        if isinstance(time, datetime.datetime):
            time = HistoryEntry.Date(time)
        else:
            try:
                time = HistoryEntry.Date(datetime.datetime.strptime(time, "%m/%d/%y, %H:%M"))
            except ValueError:
                try:
                    time = HistoryEntry.Date(datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S"))
                except ValueError:
                    time = HistoryEntry.Date(datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f"))
        self = super(HistoryEntry, cls).__new__(cls, filename, frame, time, radii)
        return self


class CutoffHistory(object):
    def __init__(self, config_filepath=DEFAULT_CONFIG_FILE):
        self._config_filepath = config_filepath
        self._history = None
        self.read()

    def read(self):
        try:
            with open(self._config_filepath, "r") as f:
                history_json = json.load(f)
            #  for elem in history_json:
            #  elem[3] = {elem.encode('utf-8'): value for elem, value in elem[3]}
            self._history = [HistoryEntry(*entry) for entry in history_json]
        except IOError:
            self._history = []

    def save(self):
        def serialization_helper(obj):
            if isinstance(obj, HistoryEntry.Date):
                return obj.datetime_obj.isoformat()
            else:
                print(type(obj))
                raise TypeError

        try:
            history = []
            for entry in self.history:
                radii = {}
                for elem in entry[3]:
                    orig = elem
                    if isinstance(elem, bytes):
                        elem = elem.decode("utf-8")
                    radii[elem] = entry[3][orig]
                history.append(HistoryEntry(entry[0], entry[1], str(entry[2]), radii))
            with open(self._config_filepath, "w") as f:
                json.dump(history, f, default=serialization_helper)
        except IOError:
            logger.warn("Could not save cutoff radii history")
            raise

    def filtered_history(
        self,
        elements,
        entries_with_additional_elements=True,
        preferred_filenames_with_frames=None,
    ):
        elements = set(elements)
        filtered_history = []
        for entry in self._history:
            current_elements = set(entry.radii.keys())
            if (entries_with_additional_elements and elements.issubset(current_elements)) or (
                not entries_with_additional_elements and elements == current_elements
            ):
                filtered_history.append(entry)
        if preferred_filenames_with_frames is not None:

            def key_func(entry):
                """Key function thats for sorting by filenames. It preferres filenames from a given list by using
                integer weights.
                """
                if entry.filename in preferred_filenames_with_frames:
                    if entry.frame in preferred_filenames_with_frames[entry.filename]:
                        weight = 0
                    else:
                        weight = 1
                else:
                    weight = 2
                return (weight, entry.filename)

            filtered_history.sort(key=key_func)
        return filtered_history

    @property
    def history(self):
        return list(self._history)

    def add(self, entry):
        self._history.insert(0, entry)

    def extend(self, entry_list):
        entry_list = sorted(entry_list, key=lambda x: x.time, reverse=True)
        for entry in entry_list:
            self.add(entry)

    def remove(self, entry):
        self._history.remove(entry)

    def remove_list(self, entry_list):
        for entry in entry_list:
            self.remove(entry)


cutoff_history = CutoffHistory()
