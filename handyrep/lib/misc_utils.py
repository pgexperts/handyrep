# this module contains a bunch of miscellaneous
# formatting and general glue functions for handyrep
# none of these functions expect access to the dictionaries

from datetime import datetime

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
    return message

def get_nested_val(mydict, *args):
    newdict = mydict
    for key in args:
        try:
            newdict = newdict[key]
        except:
            return None

    return newdict

    