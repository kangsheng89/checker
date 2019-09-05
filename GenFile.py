import os
import sys
sys.path.append(os.path.abspath(os.getcwd()+'/../../../TL109A_SwcSuprt/tools'))
import re
import shutil
import time
import subprocess
import argparse

import glob
import mako.template
import nxtr
import swcsuprt


tool_path = ''

component_impl_path = ''


def _main():


    global tool_path
    global component_impl_path
    global comp_name
    tool_path = os.getcwd()
    component_impl_path = os.path.abspath(tool_path+"./../../")
    
    parser = argparse.ArgumentParser(description='Run SWCSupport Gen file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-pre', action='store_true', default=False, 
                    dest='bo_pre',
                    help='Generate File for Pre-Analysis')
                    
    group.add_argument('-post', action='store_true', default=False, 
                dest='bo_post',
                help='Generate File for Post-Analysis')
                
    parser.add_argument('-z', action='store_true', default=False, 
            dest='bo_zip',
            help='Zipped generated file')
    
    args = parser.parse_args()
    
    
    #override all the constant and resolved the path
    override_swcsuprt_constants() 
    
    com =  swcsuprt._Component(component_impl_path)
    
    comp_name = com.name[:-5]
    
    if (args.bo_pre & args.bo_post & args.bo_zip ) is False:
        parser.print_help()
        
    else:
        # -pre
        if args.bo_pre is True:
            status, res = pre_analysis(com)
            if status!=0:
                print('\n'.join(res))
            else:
                print res[0]
        # -post
        if args.bo_post is True:
            status, res = post_analysis(com)
            if status!=0:
                print('\n'.join(res))
            else:
                print res[0]
        
        # -z
        if args.bo_zip is True:
            status, str = com.zip_polyspace()
            print str
    

        
def pre_analysis(comp):

    ddpath = os.path.join(os.path.normpath(os.path.join(component_impl_path, '..')), comp_name + '_Design', 'Design', comp_name + '_DataDict.m')
    pre_gen = [ comp.generate_greenhills(),
                comp.generate_davinci(),
                comp.generate_integration_files(),
                comp.generate_generation_script(),
                comp.generate_polyspace_files(ddpath),
                generate_sandbox_prj(swcsuprt,comp)
              ] 
              
    return pre_post_analysis(pre_gen, 'Pre')
    

def post_analysis(comp):

    post_gen = [comp.create_reports() ]
    return pre_post_analysis(post_gen, 'Post')

def pre_post_analysis(list, pre_post):

    status = 0
    res = []
    for func in list:
        stat, result = func
        res.append (result)
        status += stat
        
    if status == 0:
        res.insert(0, pre_post + ' Analysis File Gen Successful !!!')
    
    else:
        res.insert(0, pre_post + ' Analysis File Gen Failed !!!')
        
    return status, res
    
def override_swcsuprt_constants():
    # general constants
    swcsuprt._window_title = 'SWC Support'
    swcsuprt._script_dir = os.path.abspath(os.getcwd()+'/../../../TL109A_SwcSuprt/tools')
    swcsuprt._template_dir = os.path.join(swcsuprt._script_dir, 'template')
    swcsuprt._doc_dir = os.path.normpath(os.path.join(swcsuprt._script_dir, '..', 'doc'))
    swcsuprt._help_doc_path = os.path.join(swcsuprt._doc_dir, 'SwcSuprt_Usage.docx')

    # migration constants
    swcsuprt._swcsupport_launcher_file = os.path.join(swcsuprt._template_dir, 'SWCSupport.bat');

    # DaVinci constants
    swcsuprt._davinci_template_file = os.path.join(swcsuprt._template_dir, 'Component.dpa.tpl')
    swcsuprt._ecuc_template_dir = os.path.join(swcsuprt._template_dir, 'ECUC')
    swcsuprt._component_ecuc_template = os.path.join(swcsuprt._template_dir, 'Component.ecuc.arxml.tpl')

    # Green Hills project constants
    swcsuprt._greenhills_template_file = os.path.join(swcsuprt._template_dir, 'GreenHillsProject.gpj.tpl')

    # Sandbox project constants
    swcsuprt._sandbox_template_file = os.path.join(swcsuprt._template_dir, 'Sandbox.gpj.tpl')

    # integration script constants
    swcsuprt._integrate_template_file = os.path.join(swcsuprt._template_dir, 'Integrate.bat.tpl')
    swcsuprt._settings_template_file = os.path.join(swcsuprt._template_dir, 'Settings.xml.tpl')

    # generation script constants
    swcsuprt._generate_template_file = os.path.join(swcsuprt._template_dir, 'Generate.bat.tpl')

    # polyspace constants
    swcsuprt._codeprover_template_file = os.path.join(swcsuprt._template_dir, 'Polyspace.psprj.tpl')
    swcsuprt._bugfinder_template_file = os.path.join(swcsuprt._template_dir, 'Polyspace.bf.psprj.tpl')
    swcsuprt._misra_template_file = os.path.join(swcsuprt._template_dir, 'MISRASettings.cfg')
    swcsuprt._stub_c_template_file = os.path.join(swcsuprt._template_dir, 'Rte_Stubs.c.tpl')
    swcsuprt._stub_h_template_file = os.path.join(swcsuprt._template_dir, 'Rte_Stubs.h.tpl')
    swcsuprt._math_stubs_template_file = os.path.join(swcsuprt._template_dir, 'math_stubs.h')
    #_globals_template_file = os.path.join(_template_dir, 'CDD_MotCtrlMgr_Data.h.tpl')
    swcsuprt._bugfinder_report_template_file = os.path.join(swcsuprt._template_dir, 'BugFinder.rpt')
    swcsuprt._codeprover_report_template_file = os.path.join(swcsuprt._template_dir, 'Developer.rpt')


def generate_sandbox_prj(obj,comp):
    """Generate Sandbox project file.
    
    Return error code and completion message.  If erronious, message
    contains error information.
    """
    files_changed = False
    
    sandbox_name = comp.name[:-5]
    
    # render project file from sandbox template
    sandbox_template = mako.template.Template(filename=obj._sandbox_template_file)
    sandbox_rendered = sandbox_template.render(component=comp).replace('\r', '')
    
    # determine target file name
    file_path = os.path.join(comp.parent_dir, sandbox_name + '_Sandbox' + '.gpj')  
    
    # compare files (don't update if there are no differences)
    files_changed |= nxtr.write_if_changed(sandbox_rendered, file_path)

    
    # return response message
    if files_changed:
        msg = 'The sandbox project was created successfully.'
    else:
        msg = 'The sandbox project is already up to date.'
    return 0, msg

if __name__ == '__main__':
    _main()