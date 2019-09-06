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

codeprover_xml_path = './../../doc/Polyspace/CodeProver_xml_files/'
orange_path = ''
red_path = ''
gray_path = ''
misra_error_path = ''
misra_warning_path = ''
unreachable_branch_path = ''


def _main():

    global tool_path
    tool_path = os.getcwd()
    component_impl_path = os.path.abspath(tool_path+"./../../")
    component_impl_src_path = os.path.abspath(component_impl_path+"/src/")
    #get list of file with c extension under impl/src

    df = pd.read_csv(df,src_list)
    
    if df is not None:
        print df
        #df.to_csv(component_impl_src_path+'/'+str(strx)+'.csv')
        for i in range(len(df)):
            # print df.iloc[i].title
            #print df
            pattern_str = '^[A-z]:\\\\([A-z0-9-_+]+\\\\)*([A-z0-9]+\.(c|C))$'
            pattern = re.compile(pattern_str)
            result = pattern.match(df.iloc[i].title)
            
            # the title column is matching long path format
            if result is not None:
                path = df.iloc[i].title
            else :
                path = os.path.abspath(component_impl_src_path + '/' + df.iloc[i].title)
                
            # check the warning justification inside code
            #warn, line = check_warning (path , df.iloc[i].Line, df.iloc[i].Rule)
            
def list_file(dir):

    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(dir):
        for file in f:
            if '.csv' in file[-2:]:
                files.append(file)
        
    return files
    
def check_warning(path, linenumber,rule_ID):
    line = ''
    file = open(path, 'r')
    contents = file.readlines()
    warning = False
    if linenumber >= 0:
        index = int(linenumber)-1
        print contents[index]
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
    
    



#main function
if __name__ == '__main__':
    _main()