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
    global csv_folder
    tool_path = os.getcwd()
    csv_folder = os.path.abspath(tool_path+'/csv_result')
    #create result folder
    if os.path.exists(csv_folder) is False:
        os.mkdir(csv_folder)
        
    component_impl_path = os.path.abspath(tool_path+"./../../")
    component_impl_src_path = os.path.abspath(component_impl_path+"/src/")
    #get list of file with c extension under impl/src
    src_list = list_file(component_impl_src_path)
  
    get_xfrag_file()

    checker = {
        misra_error_path:'misra_error' ,
        misra_warning_path:'misra_warning' ,
        orange_path:'orange' ,
        red_path:'red' ,
        gray_path:'gray' ,
        unreachable_branch_path:'unreachable_branch' 
    }

    checker_res = []
    for k,v in checker.items():
    
        csv_file = os.path.abspath(csv_folder+'/'+v+'.csv')
        res, df = get_contents(k)
       
        if res is False :
            #filter dataframe with only src file from the src folder
            df = matchstr_in_df(df,src_list)
            
            if df is not None:
                if os.path.exists(csv_file) is True:
                    os.remove(csv_file)
                print 'Generated '+v+'.csv'
                df.to_csv(csv_file)
        else:
            checker_res.append (df)


    file = csv_folder+'\pass_result.txt'
    if os.path.exists(file) is True:
        os.remove(file)
    print 'Generated pass_result.txt'
    print_to_file(file, '\n'.join(checker_res))
    
    sys.exit(0)
    
                
def list_file(dir):

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

def print_to_file(file, s):

    f= open(file,"a+")
    f.write(s)
    f.write('\n')
    f.close()

#main function
if __name__ == '__main__':
    _main()