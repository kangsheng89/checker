import os
import sys
import re
import shutil
import sys
import time
import subprocess
import argparse
import xml.etree.ElementTree as ET

source_path = []
include_path = []
target_flag = []
module_flag= []



polyspace_root_path = "C:\\Program Files\\MATLAB\\R2013b\\polyspace"

bugfinder_rpt_template_path = polyspace_root_path +'\\toolbox\\psrptgen\\templates\\bug_finder\\'

polyspace_exe_path = ''
project_path = ''
tool_path = ''
buffstring =''
option_command_path =''
source_command_path =''
component_impl_path = ''


def _main():


    global tool_path
    global component_impl_path
    tool_path = os.getcwd()
    component_impl_path = os.path.abspath(tool_path+"./../../")
    
    t0 = time.time()
    parser = argparse.ArgumentParser(description='RunPolyspace Analysis')
    parser.add_argument('psprj_file', type=str, help='Polyspace project file')
    
    args = parser.parse_args()

    psprj_path = os.path.abspath(args.psprj_file)
    
    if os.path.isfile(psprj_path) and (os.path.splitext(psprj_path)[1]==".psprj"):
        print "===================================================================="
        print " Processing......                                                   "
        print "===================================================================="
        print "Parsing input file: " + psprj_path
        
        tree = ET.parse(psprj_path)
        root = tree.getroot()

        process_root(root, psprj_path)
        if not os.path.exists(project_path):
            print "Create Project: " + project_path
            os.mkdir(project_path)


        print "Polyspace Analysis: " + polyspace_tool
        polyspace_exe (polyspace_tool)

        process_include(root)
        process_module(root)

        process_source(root)
       
        gen_launch_polyspace()
        print "===================================================================="
        print " Running Analysis                                                   "
        print "===================================================================="
        
        subprocess.call( project_path+"\launchingCommand.bat")
        
        t1 = time.time()
        total = t1-t0
        
        print "===================================================================="
        print " Elapsed Time: "+ str(total) +"s"
        print " Ending Time: "+time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        print "===================================================================="
        print " Success! Analysis Done!!!!                                         "
        print "===================================================================="
        
        
        
    else:
    
        print " Ending Time: "+time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        print "===================================================================="
        print " Failed: Incorrect path or file extentions                          "
        print "===================================================================="
        raise IOError("Can't find Polyspace psprj file")
    
def process_source(root):

    source_list = root.find('source')
    for source in source_list:
        source_file = source.attrib['path'].replace("file:/", "").replace("/", "\\")
        source_path.append(source_file)
        
    f= open(source_command_path,"w+")
    f.write('\n'.join( source_path ) )
    f.close()
    
    
def process_include(root):

    include_list = root.find('include')
    for include in include_list:
        include_dir = include.attrib['path'].replace("file:/", "").replace("/", "\\")
        
        include_dir = '-I ' + include_dir 
        include_path.append(include_dir)
        
    f= open(option_command_path,"w+")
    f.write('# Options file\n')
    f.write('\n'.join( include_path ) )
    f.write('\n')
    f.close()
        
def process_root(root, psprj_path):

    global project_path
    global option_command_path
    global source_command_path
    global lang
    global polyspace_tool
    
    
    #print psprj_path
    curr_psprj =  os.path.dirname(os.path.abspath(psprj_path))
    prog = '-prog ' + root.attrib['name']
    version = '-verif-version '+root.attrib ['version']
    author = '-author '+ root.attrib ['author']
    lang = '-lang ' + root.attrib ['language']
    polyspace_tool = root.attrib ['source']
    
    module = root.find('module')
    result_dir = module.find('result')
    project_path = result_dir.find('file').attrib['path'].replace("file:/", "").replace("/", "\\")
    
    #change project path to current directory
    if polyspace_tool == 'Bug Finder':
        temp_path = curr_psprj + '\\~BugFinder\\'
        project_path = temp_path
        
    elif polyspace_tool == 'Code Prover':
        temp_path = curr_psprj+'\\~CodeProver\\'
        project_path = temp_path
        
    option_command_path = project_path+"options_command.txt"
    source_command_path = project_path+"sources_command.txt"
    
    #print option_command_path
    
    global buffstring
    buffstring += prog+ '\n'
    buffstring += version+ '\n'
    buffstring += author+ '\n'
    buffstring += '-sources-list-file '+ source_command_path
    

def process_target(root):

    target_options = root.find('target')
    target_language = target_options.attrib ['language']
    target_name = target_options.attrib ['name']
    for option in target_options:
        flagname = option.attrib['flagname']
        flagname_content = option.text
        
        #default 32bit, will not added into option
        if flagname == '-align':
            if flagname_content != '32':
                target_flag.append(flagname+' '+flagname_content)

        #default is signed, will not added into option
        elif flagname == '-default-sign-of-char':
            if flagname_content == 'unsigned':
                target_flag.append(flagname+' '+flagname_content)

        else:
            target_flag.append(flagname)
    
    #searching for dialect flag, default is set to none
    r = re.compile("-dialect*")
    dialect_flag = filter(r.match, target_flag) 
    if len(dialect_flag) == 0 :
        target_flag.append('-dialect none')
        
        
    print_to_file('\n'.join( target_flag ) )

def process_module(root):
    module = root.find('module')
    module_path = module.attrib ['path'].replace("file:/", "").replace("/", "\\")
    
    optionset = module.find('optionset')
    module_opt = optionset.iter('option')
    flagname_list = []
    
    for opt in module_opt:
        flagname = opt.attrib['flagname']
        flagname_list.append(flagname)
        flagname_content = opt.text

        if (flagname == '*_checkers_preset') & (flagname_content == 'all'):
             module_flag.append ('-checkers ' + flagname_content)

        if flagname == '-D' :
            for elements in opt.iter('element'):
                module_flag.append (flagname + ' ' + elements.text)
                
        if flagname == '-main-generator-writes-variables' :
            module_flag.append( flagname + ' ' + opt.text)
            
        if flagname == '-misra2' :
            for elements in opt.iter('element'):
                module_flag.append(flagname + ' ' + elements.text.replace("file:/", "").replace("/", "\\"))
        
        if flagname == '-data-range-specifications' :
            module_flag.append( flagname + ' ' + opt.text.replace("file:/", "").replace("/", "\\"))
            
        if flagname == '-includes-to-ignore' :
            str =','.join(elements.text.replace("file:/", "").replace("/", "\\") for elements in  opt.iter('element'))
            module_flag.append( flagname + ' ' +str)
        
        if flagname == '-target' :
            module_flag.append( flagname + ' ' + opt.text)
            
        if ('-report-template' in flagname) :
            module_flag.append ('-report-template ' +bugfinder_rpt_template_path + opt.text+'.rpt')
             
        if flagname == '-report-output-format' :
            module_flag.append( flagname + ' ' + opt.text)

    if '-OS-target' not in flagname_list:
        module_flag.append( '-OS-target no-predefined-OS')
        
    if '-main-generator' not in flagname_list:
        module_flag.append( '-main-generator')
        
    if '-main-generator-calls' not in flagname_list:
        module_flag.append( '-main-generator-calls unused')
        
    if '-scalar-overflows-checks' not in flagname_list:
        module_flag.append( '-scalar-overflows-checks signed')
        
    if '-scalar-overflows-behavior' not in flagname_list:
        module_flag.append( '-scalar-overflows-behavior truncate-on-error') 
        
    if '-O2' not in flagname_list:
        module_flag.append( '-O2') 
    
    if '-to Software Safety Analysis level 4' not in flagname_list:
        module_flag.append( '-to Software Safety Analysis level 4') 
        
    prepare_print_module(root)
        
        
def prepare_print_module(root):


    global project_path 
    #check if os is windows, set option dos
    if os.name == 'nt':
        os_type = '-dos'
    else:
        os_type = ''
        
    print_to_file(buffstring)
    
    status, results = match_occurance ("-OS-target", '\n')
    if (status == True):
        print_to_file (results)
    
    status, results = match_occurance ("RH850", ' ')
    if (status == True):
        print_to_file (results.replace("RH850", "mcpu"))
        process_target(root)
    
    status, results = match_occurance ("-D", '\n')
    if (status == True):
        print_to_file (results)
        
    print_to_file(os_type)


    status, results = match_occurance ("-misra2", '\n')
    if (status == True):
        print_to_file (results)
        
    status, results = match_occurance ("-includes-to-ignore", '\n')
    if (status == True):
        print_to_file (results)
    
    if  polyspace_tool == 'Bug Finder':
        status, results = match_occurance ("-checkers", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-report-template", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-report-output-format", '\n')
        if (status == True):
            print_to_file (results)
        
        print_to_file ('-import-comments ' + project_path[:-1]+ '\n')
        
    elif polyspace_tool == 'Code Prover':

        status, results = match_exact ("-main-generator", '\n')
        if (status == True) :
            print_to_file (results)
            
        status, results = match_occurance ("-main-generator-writes-variables", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-main-generator-calls", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-data-range-specifications", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-scalar-overflows-checks", '\n')
        if (status == True):
            print_to_file (results)
        
        status, results = match_occurance ("-scalar-overflows-behavior", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_exact ("-O2", '\n')
        if (status == True):
            print_to_file (results)
            
        status, results = match_occurance ("-to Software Safety Analysis", '\n')
        if (status == True):
            print_to_file (results)

def match_occurance(s, result_mod):
    matches = (x for x in module_flag if s in  x)
    #print matches
    result = result_mod.join(matches)
    if (is_not_blank(result) ) :
        status = True
        
    else:
        status = False
     
    return status , result
    

def match_exact(s, result_mod):
    matches = (x for x in module_flag if s ==  x)
    #print matches
    result = result_mod.join(matches)
    if (is_not_blank(result) ) :
        status = True
        
    else:
        status = False
     
    return status , result

def print_to_file(s):
    f= open(option_command_path,"a+")
    f.write(s)
    f.write('\n')
    f.close()
    
    
def gen_launch_polyspace():

    print "Generate batch file " 
    print project_path+"launchingCommand.bat"
    
    f= open(project_path+"launchingCommand.bat","w+")
    f.write('@echo off\n')
    f.write('"'+polyspace_exe_path+'" ')
    f.write(lang+ ' ')
    
    f.write('-options-file '+ '"'+option_command_path+'" ')
    f.write('-results-dir '+ '"'+project_path[:-1]+'" ')
    
    f.write('> '+ '"'+project_path+'rtelog" ')
    
    f.write('2>&1')
    f.close()
    
def polyspace_exe(s):

    global polyspace_exe_path
    if s == "Code Prover":
        tool_exe = "\\bin\\polyspace-code-prover-nodesktop.exe"
        
    elif s == "Bug Finder":
        tool_exe = "\\bin\\polyspace-bug-finder-nodesktop.exe"
    
    polyspace_exe_path = polyspace_root_path + tool_exe
    
def is_not_blank(s):
    return bool(s and s.strip())

#main function
if __name__ == '__main__':
    _main()