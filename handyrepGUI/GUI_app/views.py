__author__ = 'kaceymiriholston'
from flask import render_template, redirect, url_for, request, abort

import requests

from GUI_app import app
import Dictionary
from forms import AddressForm, FunctionForm


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
    elif section_name == "availability":
        section = Dictionary.Availability
    elif section_name == "action":
        section = Dictionary.Action
    else:
        section = None
    return section


@app.route('/')
@app.route('/index/')
def index():
    return render_template("base.html", topics=topic_list)


@app.route('/get_address/', methods=['GET', 'POST'])
def address():
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
            return render_template('get_address.html', form=form, message=message)
        if r.status_code in range(400, 500):
            if r.status_code == 404:
                return redirect(url_for("page_not_found"))
            message = "Please check username and password"
            return render_template('get_address.html', form=form, message=message)
        return redirect(request.args.get('next') or '/index')
    return render_template('get_address.html', form=form)


@app.route('/<topic>/')
def information(topic):
    sections = get_section(topic)
    if sections is None:
        abort(404)
    return render_template("Section.html", topics=topic_list, topic=topic, Sections=sections)


@app.route('/<topic>/<function>/', methods=['GET', 'POST'])
def function(topic, function):

    sections = get_section(topic)
    global function_parameters
    function_parameters = {}
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("address", next=request.url))
    else:
        for functions in sections:
            if functions["function_name"] == function:
                if functions["params"] is None:
                    function_parameters = None
                    url = '/%s/%s/results/' % (topic, functions["function_name"])
                    return redirect(url)
                else:
                    form = FunctionForm()
                    if form.validate_on_submit():
                        t_f = 1#This enables us to produce the number of form items needed. Please inform if there is a more streamline way to do this.
                        txt = 1

                        for params in functions['params']:

                            if params['param_type'] == 'text' or params['param_type'] == 'choice':
                                if params["required"] and getattr(form, 'textdata%d' % txt).data == "":
                                    message = "Please enter the required field."
                                    return render_template("function_detail.html", topics=topic_list, Sections=sections,
                                                           topic=topic, function=functions, form=form, message=message)
                                if not getattr(form, 'textdata%d' % txt).data == "":#Don't want to send blank data
                                    function_parameters[params['param_name']] = getattr(form, 'textdata%d'%txt).data
                                txt += 1

                            elif params['param_type'] == 'bool':
                                function_parameters[params['param_name']] = getattr(form, 'true_false%d'%t_f).data
                                t_f += 1
                        url = '/%s/%s/results' % (topic, functions["function_name"])
                        return redirect(url)
                    return render_template("function_detail.html", topics=topic_list, Sections=sections,
                                           topic=topic, function=functions, form=form)

        abort(404)


@app.route('/<topic>/<function>/results/')
def results(topic, function):
    sections = get_section(topic)
    if handyrep_address is None or username is None or password is None:
        return redirect(url_for("address", next=request.url))
    else:
        for functions in sections:
            if functions["function_name"] == function:
                url_to_send = "{address}/{function_name}".format(address=handyrep_address,  function_name = functions["function_name"])
                if function_parameters is None:
                    x = requests.get(url_to_send, auth=(username, password))
                else:
                    x = requests.get(url_to_send, params=function_parameters, auth=(username, password))
                if not x.status_code == requests.codes.OK:
                    result_to_send = "Parameters were not entered correctly. Please renter them. Remember, handyrep is case sensitive."
                    return render_template("results.html", topics=topic_list, Sections=sections, topic=topic, function=functions, result_to_send=result_to_send)
                result_to_send = x.json()
                print x.text
                return render_template("results.html", topics=topic_list, Sections=sections, topic=topic, function=functions, result_to_send=result_to_send)
        abort(404)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


