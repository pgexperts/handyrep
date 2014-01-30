import inspect
from threading import Thread
import time
import json

from flask import Flask, request, jsonify, Response

import daemon.config as config

from daemon.invokable import INVOKABLE
from daemon.periodic import PERIODIC
from daemon.startup import startup
from daemon.auth import authenticate, REALM

#

app = Flask(__name__)

#

@app.route("/<func>")
def invoke(func):
    try:
        function_reference = INVOKABLE[func]
    except KeyError:
        return jsonify({ 'Error' : 'Undefined function ' + func }) 
        
    arguments = {}
        
    for key in request.args.keys():
        arg = request.args.getlist(key)
        if len(arg) == 1:
            arguments[key] = arg[0]
        else:
            arguments[key] = arg
    
    
    if inspect.getargspec(function_reference).keywords is None:
        kwargs = inspect.getargspec(function_reference).args

        diff = set(arguments.keys()).difference(set(kwargs))
    
        if diff:
            return jsonify({ 'Error' : 'Undefined argument: ' + ', '.join(diff) })
        
    if not authenticate(func, arguments, function_reference, request):
        return Response("Could not authenticate", 401,
            {'WWW-Authenticate': 'Basic realm="%s"' % REALM})
    
    result = function_reference(**arguments)
    
    if not isinstance(result, basestring):
        result = json.dumps(result)
        
    return Response(result, mimetype='application/json')
    


def run_periodic(func):
    try:
        function_reference = PERIODIC[func]
    except KeyError:
        return  
    
    argument = None
    result = None
    
    while(True):
        result = function_reference(argument)

        if result is None or type(result) is not tuple or len(result) != 2:
            break
        
        sleep_period = int(result[0])
        
        if sleep_period > 0:
            time.sleep(sleep_period)
        
        argument = result[1]

    print func, "exiting with return", result


startup()

for func_name in PERIODIC.keys():
    t = Thread(target=run_periodic, args=(func_name,) )
    t.daemon = True
    t.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0")