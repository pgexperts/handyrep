__author__ = 'kaceymiriholston'
from flask import render_template, redirect, url_for, g, flash, request

import requests

from GUI_app import app
import Dictionary
from forms import AddressForm, FunctionForm
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField

global handyrep_address
handyrep_address = None
global username
username = None
global password
password = None
topic_list = Dictionary.Categories


def get_section(section_name):
    section = ""
    if section_name == "information":
        section = Dictionary.Information
        name = "Information"
    elif section_name == "availability":
        section = Dictionary.Availability
        name = "Availability"
    elif section_name == "action":
        section = Dictionary.Action
        name = "Action"
    else:
        name = "Please select one of the options from above"
    return {'Sections': section, 'name': name}

@app.route('/')
@app.route('/index/')
def index():
    return render_template("base.html", topics= topic_list)

@app.route('/get_address/', methods=['GET', 'POST'])
def address():
    form = AddressForm()
    message = None
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
            return render_template('get_address.html', form = form, message = message)
        if r.status_code in range(400,500):
            message = "Please check username and password"
            return render_template('get_address.html', form = form, message = message)



        return redirect(request.args.get('next') or '/index')#TODO save what was clicked on
    return render_template('get_address.html',
        form = form)

@app.route('/<topic>/')
def information(topic):
    c = get_section(topic)
    return render_template("Section.html", topics=topic_list, Sections = c['Sections'], name = c['name'])

@app.route('/<topic>/<function>/', methods=['GET', 'POST'])
def function(topic, function):

    c = get_section(topic)
    global function_parameters
    function_parameters = {}
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("address", next = request.url))
    else:
        for functions in c['Sections']:
            if functions["function_name"] == function:

                if functions["params"] == None:
                    url = '/%s/%s/none/'%(topic, functions["function_name"])
                    return redirect(url)
                else:
                    form = FunctionForm(section = c['Sections'], function = function)
                    if form.validate_on_submit():
                        tf = 1
                        tx = 1

                        for params in functions['params']:

                            if params['param_type'] == 'text' or params['param_type'] == 'choice':
                                if params["required"] and getattr(form, 'textdata%d'%tx).data == "":
                                    message = "Please enter the required field."
                                    return render_template("function_detail.html", topics=topic_list, Sections = c['Sections'],
                                           name = c['name'], topic = topic, function = functions, type = topic, form = form, message = message)
                                if not getattr(form, 'textdata%d'%tx).data == "":
                                    function_parameters[params['param_name']] = getattr(form, 'textdata%d'%tx).data
                                tx += 1

                            elif params['param_type'] == 'bool':
                                function_parameters[params['param_name']] = getattr(form, 'true_false%d'%tf).data
                                tf += 1
                        url = '/%s/%s/results'%(topic, functions["function_name"])
                        return redirect(url)
                    return render_template("function_detail.html", topics=topic_list, Sections = c['Sections'],
                                           name = c['name'], topic = topic, function = functions, type = topic, form = form)

@app.route('/<topic>/<function>/<results>/')
def results(topic, function, results):
    c = get_section(topic)
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("address", next = request.url))
    else:
        for functions in c['Sections']:
            if functions["function_name"] == function:
                url_to_send = "{address}/{function_name}".format(address=handyrep_address,  function_name = functions["function_name"])
                print url_to_send
                print function_parameters
                if results == "none":
                    x = requests.get(url_to_send, auth=(username, password))
                else:
                    x = requests.get(url_to_send, params = function_parameters, auth=(username, password))
                break
        if not x.status_code == requests.codes.OK:
            result_to_send = "Parameters were not entered correctly. Please renter them. Remember, handyrep is case sensitive."
            print x.text
            return render_template("results.html", topics=topic_list, Sections = c['Sections'], name = c['name'], topic = topic, function = functions, result_to_send = result_to_send)
        result_to_send =  x.json()
        print result_to_send
        return render_template("results.html", topics=topic_list, Sections = c['Sections'], name = c['name'], topic = topic, function = functions, result_to_send = result_to_send)


