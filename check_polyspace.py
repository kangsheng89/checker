import os
import sys
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd


complexity_thd = 10
misra_report_path = './../Polyspace/~CodeProver/Polyspace-Doc/MISRA-C-report.xml'
codemetric_report_path = './../Polyspace/~BugFinder/Polyspace-Doc/Code_Metrics.xml'


def _main():
    print os.getcwd()
    misra_status = False
    codemetric_status = False
    misra_status = misra_check()
    codemetric_status = codemetric_check()
    
    
    #check_warning()
    log(misra_status, codemetric_status)

def misra_check():

    warning_count = 0
    if os.path.isfile(misra_report_path) == True:

        tree = ET.parse(misra_report_path)
        root = tree.getroot()
        
        #iterate for all the rule tag
        rules = root.iter ('Rule')
        for item in rules:
        
            location = item.find ('Loc')
            msg = item.find ('Message')
            warning_msg = location.attrib ['File'] +", L "+ location.attrib ['Line']+ "\n\r"
            warning_msg = warning_msg + '\n\r' + item.attrib['Name'] + " "
            msgtxt = msg.text.replace ('\n', ' '). strip()
            column = int(location.attrib ['Column'])
            spacechar =' '
            warning, str = check_warning(location.attrib ['File'],location.attrib ['Line'], item.attrib['Name'])
            
            if warning is True:
                warning_count = warning_count+1
                print '-----------------------------------------------------------------------------------------------------------------'
                print warning_msg + ' ' + msgtxt+'\n\r'

                print "Please fix the line below or annotate with comments!"
                print str
                print column*spacechar + '^'
                print '-----------------------------------------------------------------------------------------------------------------'
                

    else:
        warning_count = warning_count+1
        print "Unable to locate file"
        
    if warning_count > 0:
        misra_status = True
    else:
        misra_status = False
        
    return misra_status
    

def codemetric_check():

    warning_count = 0
    if os.path.isfile(misra_report_path) == True:
        tree = ET.parse(codemetric_report_path)
        root = tree.getroot()

        filelist = root.iter ('file')
        for file in filelist:
            
            function = file.iter ('function')
            for item in function:
                function_name = item.attrib['name']
                cyclomatic_complexity = item.attrib['vg']
                #if cyclomatic complexity is more than 10
                if int(cyclomatic_complexity) > complexity_thd:
                    
                    #check the metric for the local file only, include function will be ingnored
                    result = check_metric (file.attrib['name'],function_name)
                    
                    if result is True:
                    
                        warning_count = warning_count +1 
                        print file.attrib['name']
                        print function_name + ' ' + cyclomatic_complexity + '\n\r'
    else:
        warning_count = warning_count+1
        print "Unable to locate file"
        
    if warning_count > 0:
        codemetric_status = True
    else:
        codemetric_status = False
        
    return codemetric_status
                
def log(misra_status, codemetric_status):

    if codemetric_status | misra_status:
    
        if codemetric_status == False :
            print 'Code Metrics: PASS'
        else:
            print 'Code Metric: FAILED'
            
        if misra_status == False :
            print 'MISRA Checker: PASS'
        else:
            print 'MISRA Checker: FAILED'
        
        print 'POLYSPACE ANALYSIS : FAILED'
        
    else:
    
        print 'MISRA Checker: PASS'
        print 'Code Metrics: PASS'
        print 'POLYSPACE ANALYSIS : PASS'

def check_warning(path, linenumber,rule_ID):
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    warning = False
    if linenumber >= 0:
        index = int(linenumber)-1
        
        rule_ID = rule_ID.replace('.', '\.')
        pattern_str = '\*.+'+rule_ID+'.+\*'
        
        pattern = re.compile(pattern_str)
        result = re.search(pattern,contents[index])
        
        #search line before the code if there are comment
        result_2nd = re.search(pattern,contents[index-1])
       
        if (result is None) & (result_2nd is None):
            warning = True
            line = contents[index].rstrip()
            
    file.close()
    return warning, line
    
def check_metric(path, function):
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    declaration_area = ""
    start_capture= 0
    found_function = False
    
    for line in contents:
        #searchng for the comment area
        pattern = re.compile('\<\<.+declaration area.+\>\>')
        result = re.search(pattern,line)
        
        #searching for runnable name
        pattern2 = re.compile('Runnable Entity Name:')
        result2 = re.search(pattern2,line)
        
        if result is not None:
            start_capture = start_capture+1
        
        if start_capture == 1:
            declaration_area = declaration_area + line
        
        if result2 is not None:
            declaration_area = declaration_area + line
            
    #print declaration_area
    file.close()
    
    #search function inside declaration area
    pattern = re.compile(function)
    result = re.search(pattern,declaration_area)
    
    if result is not None:
        found_function = True
        
    return found_function

#main function
if __name__ == '__main__':
    _main()