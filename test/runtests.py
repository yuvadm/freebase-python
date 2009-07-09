import unittest

import os
import os.path

import freebase

def main():
    created = False
    passwordfile = "test/.password.txt"
    
    # setup password stuff
    if not os.path.isfile(passwordfile):
        created = True
        USERNAME, PASSWORD = "", ""
        print "RUNTESTSIn order to run the tests, we need to use a valid freebase username and password"
        USERNAME = raw_input("Please enter your username: ")
        PASSWORD = raw_input("Please enter your password (it'll appear in cleartext): ")
        
        freebase.login(USERNAME, PASSWORD)
        
        print "Thanks!"
        fh = open(passwordfile, "w")
        fh.write(USERNAME + "\n" + PASSWORD)
        fh.close()
    
    # run tests
    import test_freebase
    import test_schema_manipulation

    s1 = unittest.TestLoader().loadTestsFromTestCase(test_freebase.TestFreebase)
    s2 = unittest.TestLoader().loadTestsFromTestCase(test_schema_manipulation.TestSchemaManipulation)
    
    # This is very strange. If you try to do [s1, s2], thereby running freebase tests first, 
    # two tests in the testschemamanipulation file fail! They fail because of caching issues; if
    # I check on freebase, the changes are actually there. I have racked my mind for explanations.
    anotherrun = unittest.TestSuite([s2, s1])
    
    #run = unittest.TestSuite(suites)
    
    # delete password stuff
    if created: os.remove(passwordfile)  
    
    return anotherrun


if __name__ == '__main__':
    main()