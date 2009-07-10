import unittest

import os
import os.path

import freebase

import getlogindetails

def main():
    created = False
    passwordfile = "test/.password.txt"
    
    # setup password stuff
    if not os.path.isfile(passwordfile):
        created = True
        USERNAME, PASSWORD = getlogindetails.main(create_password_file=True)
    USERNAME, PASSWORD = getlogindetails.main()        
 
    
    # run tests
    import test_freebase
    import test_schema_manipulation
    import test_hardcore_schema_manipulation

    s1 = unittest.TestLoader().loadTestsFromTestCase(test_freebase.TestFreebase)
    s2 = unittest.TestLoader().loadTestsFromTestCase(test_schema_manipulation.TestSchemaManipulation)
    s3 = unittest.TestLoader().loadTestsFromTestCase(test_hardcore_schema_manipulation.TestHardcoreSchemaManipulation)
    
    # This is very strange. If you try to do [s1, s2], thereby running freebase tests first, 
    # two tests in the testschemamanipulation file fail! They fail because of caching issues; if
    # I check on freebase, the changes are actually there. I have racked my mind for explanations.
    
    # this is such a hack, and I'm sorry. The tests run 100% correct individually.
    anotherrun = unittest.TestSuite([s1, s3, s2])
    
    #run = unittest.TestSuite(suites)
    
    # delete password stuff
    if created: os.remove(passwordfile)  
    
    return anotherrun
    


if __name__ == '__main__':
    main()