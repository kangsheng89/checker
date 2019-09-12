import os
import sys
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
import glob

import numpy as np
import pandas as pd

MISRA_allow_tag =[ 1.1,  5.1,  5.3,   5.6,   5.7,   6.3,
                   6.4,  8.5,  8.8,   8.9,   8.10,  8.12,
                   11.3, 11.4, 11.5,  12.12, 13.7,  14.1,
                   14.2, 16.7, 16.10, 17.4,  18.4,  19.1,
                   19.4, 19.6, 19.7,  19.10, 19.13, 19.15, 21.1]
                   
checker_ignore = [
    'misra_error' ,
    'red' ,
    'gray']

checker= [
    'misra_warning' ,
    'orange' ,
    'unreachable_branch']
    
    
def _main():

    global tool_path
    global component_impl_src_path
    
    tool_path = os.getcwd()
    
    csv_folder = os.path.abspath(tool_path+'/csv_result')
    #create result folder
    
    component_impl_path = os.path.abspath(tool_path+"./../../")
    component_impl_src_path = os.path.abspath(component_impl_path+"/src/")
    #get list of file with c extension under impl/src
    

    if os.path.exists(csv_folder) is False:
        print "No csv_result folder"
        sys.exit(1)
        
    else:
        
        print (open_pass_res(csv_folder+'/pass_result.txt'))
        
        csv_list = list_file(csv_folder)
        count  = 0
        not_justify_dict ={}
        #res = process_csv(csv_folder+'/unreachable_branch.csv', 'unreachable_branch')
        for csv in csv_list:
            if csv[:-4] in checker:
                file = os.path.abspath(csv_folder+'/'+csv)
                res, check = process_csv(file, csv[:-4])

                if res != 0:
                    not_justify_dict.update({csv: (res, check)})
                count += res
                
            elif csv[:-4] in checker_ignore:
                count += 1
                print "Mandatory to fix errors/warnings in "+csv
                
            else:
                pass
                
        if count != 0:
        
            for (file, items) in not_justify_dict.items():
                 print str(items[0]) + ' items of warnings '+ str(items[1]) +' from '+ file + ' is not justified'
            
            print "CHECKER FAILED"
            
            sys.exit(1)
        
        else:
            
            
            for csv in csv_list:
                if csv[:-4] in checker:
                    print 'All the items in '+csv+ ' has been justified'
                    
            print "CHECKER PASS"
            sys.exit(0)
        


def process_csv(file, checker):
    #print file
    #print checker
    
    check = []
    df = pd.read_csv(file)

    if df is not None:
        #rules = (df['Rule'].unique())
        #print rules
        
        if checker == "misra_warning":
            check = list(df['Rule'].unique().astype(str))
        elif (checker == "orange") | (checker == "unreachable_branch"):
            check = list(df['Check'].unique().astype(str))
        else:
            pass
        
        count = 0
        for i in range(len(df)):
            # print df.iloc[i].title
            #print df
            warn = 0
           
            _path, file = os.path.split(df.iloc[i].title)

            pattern_str = '^[A-z]:\\\\([A-z0-9-_+]+\\\\)*([A-z0-9]+\.(c|C))$'
            pattern = re.compile(pattern_str)
            result = pattern.match(df.iloc[i].title)
            # the title column is matching long path format
            #print file
            
            if result is not None:
                path = os.path.abspath(component_impl_src_path + '/' +file)
            else :
                path = os.path.abspath(component_impl_src_path + '/' + df.iloc[i].title)

            # check the warning justification inside code
            if checker == "misra_warning":
            
                warn, line = misra(path, df.iloc[i].Line, df.iloc[i].Rule)
                if (warn is 0) & (str(df.iloc[i].Rule) in check):
                    check.remove(str(df.iloc[i].Rule))
                
            elif (checker == "orange") | (checker == "unreachable_branch"):
            
                warn , line = check_polyspace_warning(path,df.iloc[i].Line, df.iloc[i].Check )
                if (warn is 0) & (str(df.iloc[i].Check) in check):
                    checkremove(str(df.iloc[i].Check))
                
            else:
            
                pass
            
            count += warn
    
    return count, check
    
    
    
def misra(path,  linenum, rule ):

    warn = 0
    # check the warning justification inside code
    if rule in MISRA_allow_tag :
        warn, line = check_misra_warning (path , linenum, str(rule))

    else:
        warn +=1
        line =  check_error (path , linenum)

    return warn, line

def list_file(dir):

    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(dir):
        for file in f:
            if '.csv' in file[-4:]:
                files.append(file)
        
    return files
    
def check_polyspace_warning(path, linenumber,check):
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    warning = 0

    if linenumber >= 0:
        index = int(linenumber)-1
        #print contents[index]
        
        pattern_str = '\*.*\[CodeProver Warning\].*'+check+'.+\*'
        #print pattern_str
        
        pattern = re.compile(pattern_str,re.I)
        result = re.search(pattern,contents[index])
        
        #search line before the code if there are comment
        result_2nd = re.search(pattern,contents[index-1])
        
        #search line before the code if there are comment
        result_3rd = re.search(pattern,contents[index-2])

       
        if (result is None) & (result_2nd is None) & (result_3rd is None):
            warning = 1
            line = contents[index].rstrip()
        
    file.close()
    return warning, line

def check_misra_warning(path, linenumber,rule_ID):

    res = find_declaration_Misra(path, rule_ID)
    
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    warning = 0
    if linenumber >= 0:
        index = int(linenumber)-1
        #print contents[index]
        rule_ID = rule_ID.replace('.', '\.')
        pattern_str = '\*.*'+rule_ID+'.*\*'
        
        pattern = re.compile(pattern_str)
        result = re.search(pattern,contents[index])
        
        #search line before the code if there are comment
        result_2nd = re.search(pattern,contents[index-1])
       
        if (result is None) & (result_2nd is None) & (res is None):
            warning = 1
            line = contents[index].rstrip()
            
    file.close()
    
        
    #print line
    #print warning
    
    return warning, line
    
def find_declaration_Misra(path, rule ):
    
    file = open(path, 'r')
    line = ''
    declaration_area = ""
    start_capture= 0
    found_function = False
    contents = file.readlines()
    
    for line in contents:

        pattern = re.compile('\<\<.+declaration area.+\>\>')
        result = re.search(pattern,line)
        
        #searching for runnable name
        pattern2 = re.compile('\<\<.+Start of runnable implementation.+\>\>')
        result2 = re.search(pattern2,line)
        
        pattern3 = re.compile('/\*.*MISRA-C:2004 Rule.+'+rule+'.*\*/')
        result3 = re.search(pattern3,line)
        
        if result is not None:
            start_capture = start_capture+1
        
        if start_capture == 1 :
            if result3 is not None:
                declaration_area = declaration_area + line
            else:
                pass
        
        if result2 is not None:
            pass
            
    file.close()
    
    if declaration_area == "":
        return None    
            
    return declaration_area 
    
def check_error(path, linenumber):
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    if linenumber >= 0:
        index = int(linenumber)-1
        line = contents[index].rstrip()
    file.close()
    return line
    
def open_pass_res(path):
    line = ''
    file = open(path, 'r')
    contents = file.read()
    file.close()
    return contents
    
    
#main function
if __name__ == '__main__':
    _main()