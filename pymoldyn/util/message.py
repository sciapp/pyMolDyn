# -*- coding: utf-8 -*-

__all__ = ["print_message",
           "progress",
           "finish",
           "error",
           "log",
           "set_output_callbacks"]


_print_message = None
_progress = None
_finish = None
_error = None
_log = None

# Buffer log messages if no valid log callback is set
_log_buffer = []


def print_message(*args):
    if callable(_print_message):
        return _print_message(*args)


def progress(*args):
    if callable(_progress):
        return _progress(*args)


def finish(*args):
    if callable(_finish):
        return _finish(*args)


def error(*args):
    if callable(_error):
        return _error(*args)


def log(*args):
    if callable(_log):
        return _log(*args)
    else:
        _log_buffer.append(args)


def set_output_callbacks(progress_func, print_func, finished_func, error_func, log_func):
    global _progress, _print_message, _finish, _error, _log

    _progress = progress_func
    _print_message = print_func
    _finish = finished_func
    _error = error_func
    _log = log_func

    if _log_buffer and _log:
        for log_args in _log_buffer:
            _log(*log_args)
        del _log_buffer[:]
