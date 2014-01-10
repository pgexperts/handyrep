import daemon.daemonfunctions as hrdf

REALM=''

def authenticate(path, arguments, function_reference, request):

    auth = request.authorization
    if not auth:
        # Require authentication on every other call
        return False
        
    username = auth.username
    password = auth.password
    funcname = function_reference.__name__

    authed = hrdf.authenticate(username, password, funcname)

    return authed
