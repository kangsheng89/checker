import os
import sys
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
from collections import OrderedDict
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
    src_list = list_file(component_impl_src_path)
  
    get_xfrag_file()
    
    
    checker = [
        misra_error_path ,
        misra_warning_path ,
        orange_path ,
        red_path ,
        gray_path ,
        unreachable_branch_path
    ]
    strx = 0
    for x in checker:
        strx +=1
        res_noerr, df = get_contents(x)
       
        if res_noerr == False :
            #filter dataframe with only src file from the src folder
            df = matchstr_in_df(df,src_list)
            
            if df is not None:
                print df
                df.to_csv(component_impl_src_path+'/'+str(strx)+'.csv')
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
                    
        else:
            print df
                
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
    
def list_file(dir):
    #dir = os.path.abspath(component_impl_path+"/src/")
    
    #print component_impl_src_path
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(dir):
        for file in f:
            if '.c' in file[-2:]:
                files.append(file)
        
    return files
    
def matchstr_in_df(table,filelist):

    empty = False
    df = pd.DataFrame(table)
    df = df[df['title'].str.contains('|'.join(filelist))]
    
    if df.empty == False:
        return df
    
def get_contents(xml_path):
    

    tree = ET.parse(xml_path)
    root = tree.getroot()
    root_title = root.find("title")
    result = []
    
    res, res_str = check_no_error(root_title.tail)
    
    
    if res == False:
        tables = root.iter("table")
        
        for table in tables:
            file = table.find("title")
            
            header = table.find("tgroup").find("thead").find("row")
            elements = header.iter("entry")
            entry_set = ["title"]
            for entry in elements:
                entry_set.append( entry.text)
        
            #construct namedtuple of type Table using tuples from the thead
            Table = namedtuple( "Table", entry_set)
            
            contents = table.find("tgroup").find("tbody").iter("row")
            
            for row in contents:
                elements = row.iter("entry")
                entry_contents_set = [file.text]
                for entry in elements:
                    entry_text = entry.text
                    
                    emphasis = entry.find("emphasis")
                    if emphasis is not None:
                        entry_text = emphasis.text
                        
                    simple_list = entry.find("simplelist")
                    if simple_list is not None:
                        member = simple_list.iter("member")
                        des = ''
                        for item in member:
                            des += item.text+'\n'
                        entry_text = des
                        
                    entry_contents_set.append(entry_text)
                         
                #unpack tuple and assign to the arg from Table type
                result.append( Table(*entry_contents_set) )
    else:

        result = res_str


    return res , result
        
def findInfiles(path, regex):
    regObj = re.compile(regex)
    res = []
    filepath = ''
    for root, dirs, fnames in os.walk(path):
        for fname in fnames:
            with open(os.path.join(root, fname)) as f:
                for line in f:
                    if regObj.search(line):
                        filepath =  os.path.join(root, fname)
                        res.append(line)
    return filepath, res
    
def get_xfrag_file():
    global orange_path
    global red_path
    global gray_path
    global misra_error_path
    global misra_warning_path
    global unreachable_branch_path
    
    orange_path, res = findInfiles(codeprover_xml_path, "Unproven Run-Time Checks")
    red_path, res = findInfiles(codeprover_xml_path, "Proven Run-Time Violations")
    gray_path,res = findInfiles(codeprover_xml_path, "Unreachable Functions")
    misra_error_path, res = findInfiles(codeprover_xml_path, "MISRA-C  Errors")
    misra_warning_path, res = findInfiles(codeprover_xml_path, "MISRA-C  Warnings") 
    unreachable_branch_path, res = findInfiles(codeprover_xml_path, "Proven Unreachable Code Branches")
    
def check_no_error(str):

    pattern = re.compile('No .+ were found.')
    result = pattern.match(str.strip())
    
    if result is not None :
        res = True
        #print no_error
    else:
        res = False
    return res, str.strip()



#main function
if __name__ == '__main__':
    _main()