"""
This file implements additional validators for WTForms content which are not
found in vanilla WTForms. These functions are patched into
flaskext.wtforms.validators so that they can be used just as any of the other
validators. They are designed to follow a similar API.
"""

from flaskext.wtf import validators, ValidationError
from datetime import datetime
from accounts.ctypescracklib import FascistCheck

def validate_date(format = '', message = ''):
    """
    Validates a date field. Format is a format suitable for strptime in the
    python datetime module. Message is a message to be used when the format
    does not match. If the format does match, the returned message will be
    the same as that from the exeption which is raised.
    
    This function is available via flaskext.wtforms.validators.Date
    """
    def validate(form, field):
        try:
            datetime.strptime(field.data, format)
        except ValueError, e:
            if format in str(e):
                raise ValidationError(message)    
            else:
                raise ValidationError(str(e))
    return validate
    
def validate_unique_column(table, column, message = ''):
    """
    Validates that a field will be unique within a given database column by 
    ensuring that it is not currently in the database.
    table is a SQLAlchemy model class.
    column is a column within table.
    message is the message to be returned if the column is not unique.
    
    This function is available via flaskext.wtforms.validators.UniqueColumn
    """
    def validate(form, field):
        count = table.query.filter(column == field.data).count()
        if count > 0:
            raise ValidationError(message)
    return validate
    
def validate_in_table(table, column, message = ''):
    """
    Validates that a field is contained within the database.
    table is a SQLAlchemy model class.
    column is a column within table.
    message is the message to be returned field is not in the table.
    
    This function is available via flaskext.wtforms.validators.EntryExists
    """
    def validate(form, field):
        count = table.query.filter(column == field.data).count()
        if count == 0:
            raise ValidationError(message)
    return validate
    
def validate_length_or_empty(min=None, max=None):
    """
    This is a convenience validator which validates that a field has a
    minimum or maximum length, unless it is empty, for use in forms that
    may have updated fields which are initially empty.
    min is the minimum field length.
    max is the maximum field length.
    
    This function is available via flaskext.wtforms.validators.LengthOrEmpty
    """
    def validate(form, field):
        if field.data == '':
            return
        if min is not None and len(field.data) < min:
            raise ValidationError("Minimum length is " + str(min))
        if max is not None and len(field.data) > max:
            raise ValidationError("Maximum length is " + str(min))
    return validate

def validate_email_or_empty():
    def validate(form, field):
        if field.data == '':
            return
        if '@' not in field.data:
            raise ValidationError("Invalid e-mail address.")
        v = validators.Email()
        v(form, field)
    return validate

def validate_cracklib():
    """
    Runs the pasword through cracklib to test strength.
    """
    def validate(form, field):
        if field.data == '':
            return
        ret = FascistCheck(field.data, form.username.data)
        if ret is not None:
            error = "Password rejected: %s." % ret
            raise ValidationError(error)
        else:
            return
    return validate
    
validators.Date = validate_date
validators.UniqueColumn = validate_unique_column
validators.EntryExists = validate_in_table
validators.LengthOrEmpty = validate_length_or_empty
validators.EmailOrEmpty = validate_email_or_empty
validators.CrackLib = validate_cracklib
