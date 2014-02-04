__author__ = 'kaceymiriholston'
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required
import Dictionary

class AddressForm(Form):
    address = TextField('address', validators = [Required()])
    username = TextField('username', validators = [Required()])
    password = TextField('password', validators = [Required()])

class FunctionForm(Form):
    textdata1 = TextField('textdata1')
    textdata2 = TextField('textdata1')
    textdata3 = TextField('textdata1')
    true_false1 = BooleanField('true_false1', default = False)
    true_false2 = BooleanField('true_false2', default = False)
    true_false3 = BooleanField('true_false3', default = False)
