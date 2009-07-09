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

    # test_freebase.TestFreebase, 
    testcases = [test_schema_manipulation.TestSchemaManipulation, test_freebase.TestFreebase]
    testcases_dumb = [test_freebase.TestFreebase, test_schema_manipulation.TestSchemaManipulation]
    
    
    suites = [unittest.TestLoader().loadTestsFromTestCase(x)
                    for x in testcases]
    
    
    suites_dumb = [unittest.TestLoader().loadTestsFromTestCase(x)
                    for x in testcases_dumb]
    
    print sorted(suites)
    print sorted(suites_dumb)
    print sorted(suites) == sorted(suites_dumb)
    
    print
    
    print "SUITES", suites


    s1 = unittest.TestLoader().loadTestsFromTestCase(test_freebase.TestFreebase)
    s2 = unittest.TestLoader().loadTestsFromTestCase(test_schema_manipulation.TestSchemaManipulation)
    
    anotherrun = unittest.TestSuite([s1, s2])
    
    #run = unittest.TestSuite(suites)
    
    # delete password stuff
    
    if created: os.remove(passwordfile)  
    
    return anotherrun


if __name__ == '__main__':
    main()