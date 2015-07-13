# -*- coding: utf-8 -*-

__all__ = ["print_message",
           "progress",
           "finish",
           "error",
           "set_output_callbacks"]


_print_message = None
_progress = None
_finish = None
_error = None


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

def set_output_callbacks(progress_func, print_func, finished_func, error_func):
    global _progress, _print_message, _finish, _error

    _progress = progress_func
    _print_message = print_func
    _finish = finished_func
    _error = error_func
