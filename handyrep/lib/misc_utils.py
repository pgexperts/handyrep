# this module contains a bunch of miscellaneous
# formatting and general glue functions for handyrep
# none of these functions expect access to the dictionaries

from datetime import datetime

def ts_string(self, some_ts):
    return datetime.strftime(some_ts, '%Y-%m-%d %H:%M:%S')

def string_ts(self, some_string):
    try:
        return datetime.strptime(some_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def now_string(self):
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
        return extra.update({ "result" : result, "details" : details })
    else:
        return { "result" : result, "details" : details }