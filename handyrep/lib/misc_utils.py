# this module contains a bunch of miscellaneous
# formatting and general glue functions for handyrep
# none of these functions expect access to the dictionaries

from datetime import datetime
import threading

def ts_string(some_ts):
    return datetime.strftime(some_ts, '%Y-%m-%d %H:%M:%S')

def string_ts(some_string):
    try:
        return datetime.strptime(some_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def now_string():
    return ts_string(datetime.now())

def succeeded(resdict):
    #checks a return_dict for success
    return (resdict["result"] == "SUCCESS")

def failed(resdict):
    # checks a return_dict for failure
    return (resdict["result"] == "FAIL")

def return_dict(succeeded, details=None, extra=None):
    # quick function for returning a dictionary of
    # results from complex functions
    if succeeded:
        result = "SUCCESS"
    else:
        result = "FAIL"

    if extra:
        extra.update({ "result" : result, "details" : details })
        return extra
    else:
        return { "result" : result, "details" : details }

def exstr(errorobj):
    template = "{0}:\n{1!r}"
    message = template.format(type(errorobj).__name__, errorobj.args)
    if not message:
        message = str(errorobj)
    return message

def get_nested_val(mydict, *args):
    newdict = mydict
    for key in args:
        try:
            newdict = newdict[key]
        except:
            return None

    return newdict

# returns the first non-None in a list
def notnone(*args):
    for arg in args:
        if arg is not None:
            return arg

    return None

# returns the first populated value in a list
def notfalse(*args):
    for arg in args:
        if arg:
            return arg

    return None

# rlock function for locking fabric access
# we need to do this because fabric is not multi-threaded

def lock_fabric(locked=True):
    lock = threading.RLock()
    if locked:
        lock.acquire()
        return True
    else:
        try:
            lock.release()
        except RuntimeError:
            # ignore it if we didn't have the lock
            return False

def fabric_unlock_all():
    unlocked = True
    while unlocked:
        unlocked = lock_fabric(False)

    return True