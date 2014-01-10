import re
import psycopg2, psycopg2.extensions
from lib.error import CustomError
import logging

# contains an assortment of random functions to make
# handling activity on psycopg2 database connections
# a bit easier

# construct a connection string and open aS postgresql
# connection using kwargs format instead of a DSN

def log_activity( message, always_log=False ):
    if always_log:
        logging.info(message)
    return

def get_pg_conn( dbname, **kwargs ):

    if not dbname:
        logging.error("No database name supplied")
        raise CustomError("DBCONN","ERROR: a target database is required.")

    connect_string = "dbname=%s " % dbname

    if "dbhost" in kwargs:
        if kwargs["dbhost"]:
            connect_string += " host=%s " % kwargs["dbhost"]

    if "dbuser" in kwargs:
        if kwargs["dbuser"]:
            connect_string += " user=%s " % kwargs["dbuser"]

    if "dbpass" in kwargs:
        if kwargs["dbpass"]:
            connect_string += " password=%s " % kwargs["dbpass"]

    if "dbport" in kwargs:
        if kwargs["dbport"]:
            connect_string += " port=%s " % kwargs["dbport"]

    if "appname" in kwargs:
        if kwargs["appname"]:
            connect_string += " application_name=%s " % kwargs["appname"]

    try:
        conn = psycopg2.connect( connect_string )
    except:
        raise CustomError("DBCONN","ERROR: Unable to connect to Postgres using the connections string %s" % connect_string)

    if "autocommit" in kwargs:
        if kwargs["autocommit"]:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    return conn

# test if a value is a number
def is_number(val):
    try:
        nval = float(val)
    except ValueError:
        return False

    return True

# do proper quote escaping for values to be inserted
# into postgres as part of an INSERT statement
def escape_val( val ):
    val = str(val)
    #if empty string, pass through
    if val == '':
        return "''"
    # check for special words true, false, and null
    specialvals = [ 'TRUE', 'FALSE', 'NULL' ]
    if val.upper() in specialvals:
        return val.upper()
    # if it's a number, don't escape it:
    if is_number(val):
        return val
    # if it's an array, it's already escaped:
    if re.match('ARRAY\[.*', val) or re.match('{.*', val):
        return "'" + val + "'"
    # if it's a string, escape all '
    val = val.replace("'","''")
    # now quote it
    val = "'" + val + "'"
    return val

# make a value string from an array
# including shifting date an timestamp values
def value_string_shift ( vallist, tslist, datelist, ref_ts, ref_date ):
    newlist = []
    for valpos, value in enumerate(vallist):
        if valpos in tslist:
            # it's a timestamp, shift it
            newval = "'%s' + INTERVAL '%s'" % (ref_ts, value, )
        elif valpos in datelist:
            # if it's a date, shift it
            newval = "'%s' + %s" % (ref_date, value )
        else:
            newval = escape_val(value)

        newlist.append(newval)

    return newlist

def insert_col_list( coldict ):
    targetlist = ', '.join(coldict.keys())
    return targetlist

def insert_values_list( coldict ):
    collist = []
    for colname, colval in coldict.iteritems():
        if colval:
            collist.append('%(' + colname + ')s')
        else:
            collist.append("DEFAULT")

    vallist = ', '.join(collist)
    return vallist

def simple_insert_statement ( tablename, coldict ):
    insertstr = "INSERT INTO %s ( %s ) VALUES ( %s ) " % (tablename, insert_col_list(coldict),insert_values_list(coldict),)
    return insertstr

def execute_it(cur, statement, params=[]):
    try:
        cur.execute(statement, params)
    except Exception, e:
        log_activity(e.pgerror, True)
        return False
    return True

def get_one_row(cur, statement, params=[]):
    try:
        cur.execute(statement, params)
    except Exception, e:
        log_activity(e.pgerror, True)
        return None
    return cur.fetchone()

def get_one_val(cur, statement, params=[]):
    try:
        cur.execute(statement, params)
    except Exception, e:
        log_activity(e.pgerror, True)
        return None
    val = cur.fetchone()
    if val is not None:
        return val[0]
    else:
        return None


