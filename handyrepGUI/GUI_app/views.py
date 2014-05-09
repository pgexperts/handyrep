__author__ = 'kaceymiriholston'
from flask import render_template, redirect, url_for, request, abort, make_response

import requests, json

from GUI_app import app
import Dictionary
from forms import AddressForm, FunctionForm, ClusterForm


global handyrep_address
handyrep_address = None
global username
username = None
global password
password = None
global function_parameters
function_parameters = {}

def get_status():
    url_to_send = "{address}/get_status".format(address=handyrep_address)
    status = requests.get(url_to_send, auth=(username, password)).json()
    return status

def get_server_info(server_name):
    params = {"servername": str(server_name)}
    url_to_send = "{address}/get_server_info".format(address=handyrep_address)
    request= requests.get(url_to_send,params=params, auth=(username,password))
    return request.json()

@app.route('/logout/')
def logout():
    global handyrep_address
    handyrep_address = None
    global username
    username = None
    global password
    password = None
    return redirect('/index')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = AddressForm()
    if form.validate_on_submit():
        global handyrep_address
        handyrep_address = form.address.data
        global username
        username = form.username.data
        global password
        password = form.password.data
        url_to_send = "{address}/get_master_name".format(address=handyrep_address)
        try:
            r = requests.get(url_to_send, auth=(username, password))
        except:
            message = "There is something wrong with the address, please try again."
            handyrep_address = None
            username = None
            password = None

            return render_template('login.html', form=form, message=message)
        if r.status_code in range(400, 500):
            if r.status_code == 404:
                return redirect(url_for("page_not_found"))
            message = "Please check username and password"

            return render_template('login.html', form=form, message=message)
        return redirect(request.args.get('next') or '/index')

    return render_template('login.html', form=form)


@app.route('/')
@app.route('/index/')
def index():
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("login"))
    status = get_status()
    return render_template("index.html", status=status)

@app.route('/server/<server_name>')
def server_actions(server_name):
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("login"))
    #status information
    status = get_status()
    #server information
    server_info = get_server_info(server_name)
    if server_info.get(server_name)["role"] == "master" or server_info.get(server_name)["role"] == "replica":
        functions = getattr(Dictionary, server_info.get(server_name)["role"])
    else:
        functions = Dictionary.other
    final_functions = sorted(functions.get(server_info.get(server_name)["enabled"]))
    return render_template("server_page.html", status=status, info=server_info, functions=final_functions)

@app.route('/cluster')
def cluster_actions():
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("login"))
    #status information
    status = get_status()
    #server information
    server_info = None
    final_functions = sorted(Dictionary.cluster_functions)
    return render_template("server_page.html", status=status, info=server_info, functions=final_functions)

@app.route('/server/<server_name>/<function>', methods=['GET', 'POST'])
def function_detail(server_name, function):
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("login"))
    #status information
    status = get_status()
    #function parameters
    server_info = get_server_info(server_name)
    function_info = Dictionary.Functions.get(function)
    if len(function_info["params"]) > 1:
        form = FunctionForm()
        if form.validate_on_submit():
            for params in function_info["params"]:
                if params["param_name"] == "servername" or params["param_name"] == "replicaserver":
                        continue
                if params["required"] and getattr(form, 'textdata').data == "":
                    message = "Please enter the required field."
                    return render_template("function_data.html", status=status, info=server_info, form=form, function = function_info, message=message)
                if params['param_type'] == 'bool':
                    if not getattr(form, 'true_false').data == params["param_default"] :#Don't want to send blank data:
                        function_parameters[params['param_name']] = getattr(form, 'true_false').data
                elif not getattr(form, 'textdata').data == "":
                    if params["param_default"] and str(getattr(form, 'textdata').raw_data[0]).lower() == params["param_default"].lower() :#Don't want to send blank data:
                        pass
                    else:
                        function_parameters[params['param_name']] = str(getattr(form, 'textdata').raw_data[0])
            return redirect(url_for("results", server_name = server_name, function=function))
        for params in function_info["params"]:
            if params["param_name"] == "servername":
                function_parameters["servername"] = server_name
            elif params["param_name"] == "replicaserver":
                function_parameters["replicaserver"] = server_name
            else:
                if params["param_default"]:
                    if params["param_type"] == "text":
                        if params["param_default"] == "current master":
                            url_to_send = "{address}/get_master_name".format(address=handyrep_address)
                            r = requests.get(url_to_send, auth=(username, password))
                            getattr(form, 'textdata').data = r.json()
                        else:
                            getattr(form, 'textdata').data = params["param_default"]
                    if params["param_type"] == "bool":
                        getattr(form, 'true_false').data = params["param_default"]
    elif len(function_info["params"]) == 1 and (function_info.get("params")[0].get("param_name") == "servername" or function_info.get("params")[0].get("param_name") == "newmaster"):
        if function_info.get("params")[0].get("param_name") == "newmaster":
            function_parameters["newmaster"] = server_name
        else:
            function_parameters["servername"] = server_name
        return redirect(url_for("results", server_name = server_name, function=function))
    return render_template("function_data.html", status=status, info=server_info, form=form, function = function_info)

@app.route('/cluster/<function>', methods=['GET', 'POST'])
def cluster_function_detail(function):
    global function_parameters
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("login"))
    #status information
    status = get_status()
    #function parameters
    server_info = None
    function_info = Dictionary.Functions[function]
    if not function_info['params']:
        function_parameters = None
        return redirect(url_for("results", server_name="cluster", function=function))
    form = ClusterForm()
    if form.validate_on_submit():
        for index, param in enumerate(function_info["params"]):
            if not param["param_type"] == 'bool':
                if param["required"] and getattr(form, 'textdata%d'%(index+1)).data == "":
                    message = "Please enter the required field."
                    return render_template("cluster_function_data.html", status=status, info=server_info, form=form, function = function_info, message=message)
                if not getattr(form, 'textdata%d' %(index+1)).data == "":
                    if param["param_default"] and str(getattr(form, 'textdata%d' %(index+1)).raw_data[0]).lower() == param["param_default"].lower() :#Don't want to send blank data:
                        pass
                    else:
                        function_parameters[param['param_name']] = str(getattr(form, 'textdata%d'%(index+1)).raw_data[0])
            else:
                if not getattr(form, 'true_false').data == param["param_default"] :#Don't send default data
                    function_parameters[param['param_name']] = getattr(form, 'true_false').data
        return redirect(url_for("results", server_name = "cluster", function=function))

    ##fill in defaults - currently only items with one form field have defaults
    if function_info["params"][0]["param_default"]:
        if function_info["params"][0]["param_type"] == "bool":
            getattr(form, 'true_false').data = function_info["params"][0]["param_default"]
        else:
            getattr(form, 'textdata1').data = function_info["params"][0]["param_default"]
    return render_template("cluster_function_data.html", status=status, info=server_info, form=form, function = function_info)


@app.route("/server/<server_name>/<function>/results/")
def results(server_name, function):
    global function_parameters
    if handyrep_address is None or username is None or password is None:
        function_parameters = {}
        return redirect(url_for("login"))

    print function_parameters
    if server_name == "cluster":
        server_info = None
    else:
        server_info = get_server_info(server_name)

    function_info = Dictionary.Functions.get(function)
    url_to_send = "{address}/{function}".format(address=handyrep_address, function = function)
    if function_parameters is None:
        x = requests.get(url_to_send, auth=(username, password))
    else:
        x = requests.get(url_to_send, params=function_parameters, auth=(username, password))
    if not x.status_code == requests.codes.OK:
        if x.status_code == 500:
            function_parameters = {}
            abort(500)
        result_to_send = "Parameters were not entered correctly. Please renter them. Remember, handyrep is case sensitive."
    else:
        result_to_send = x.json()
        #status information
    status = get_status()
    function_parameters = {}
    return render_template("results.html", status=status, info=server_info, results=function_parameters, result_to_send=result_to_send, function = function_info)




@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.errorhandler(500)
def app_error(error):
    return render_template('500_error.html'), 500


