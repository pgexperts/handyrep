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
    textdata = TextField('textdata')
    true_false = BooleanField(default = False)

class ClusterForm(Form):
    textdata1 = TextField('textdata')
    textdata2 = TextField('textdata')
    true_false = BooleanField(default=False)





