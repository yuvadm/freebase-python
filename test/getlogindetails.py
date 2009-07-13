import os
import os.path
import getpass

import freebase
from freebase.api.session import MetawebError

passwordfile = "test/.password.txt"

def main(create_password_file=False):
    USERNAME, PASSWORD = "", ""
    
    if not os.path.isfile(passwordfile):
        print "In order to run the tests, we need to use a valid freebase username and password"
        USERNAME = raw_input("Please enter your username: ")
        try:
            PASSWORD = getpass.getpass("Please enter your password: ")
        except getpass.GetPassWarning:
            PASSWORD = raw_input("Please enter your password: ")
    
        freebase.login(USERNAME, PASSWORD)
    
        print "Thanks!"
        
        if create_password_file:
            writepassword(passwordfile, USERNAME, PASSWORD)
    
    else:
        pf = open(passwordfile, "r")
        USERNAME, PASSWORD = pf.read().split("\n")
        pf.close()
        try:
            freebase.login(USERNAME, PASSWORD)
        except MetawebError, me:
            print "The username/password in your .password.txt file are incorrect"
            raise me
    
    return USERNAME, PASSWORD
    

def writepassword(passwordfile, username, password):
    fh = open(passwordfile, "w")
    fh.write(username + "\n" + password)
    fh.close()