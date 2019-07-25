def generate_polyspace_files(self, dd_path=None):
        """Generate Polyspace project files and stubs.
        
        Return error code and completion message.  If erronious, message
        contains error information.
        """
        files_changed = False
        
        # check arguments
        if dd_path is not None and not os.path.exists(dd_path):
            return 3, 'Specified data dictionary does not exist.'
        
        # set up paths
        parent_dir = os.path.normpath(os.path.join(self.path, '..'))
        print (dd_path)
        # set up standard includes
        standard_includes = (
            'TL103A_CplrSuprt/include/2013.5.5/ansi',
            'AR202A_MicroCtrlrSuprt_Impl/include/P1M/R7F701311',
            'AR200A_ArSuprt_Impl/include/ASR4.0.3',
            'AR200A_ArSuprt_Impl/tools/contract',
            'AR201A_ArCplrSuprt_Impl/include/ASR4.0.3',
            'AR201A_ArCplrSuprt_Impl/tools/contract',
            'AR100A_NxtrMath_Impl/include',
            'AR101A_NxtrIntrpn_Impl/include',
            'AR104A_NxtrFil_Impl/include',
            'AR102A_NxtrTi_Impl/include',
            'AR103A_NxtrFixdPt_Impl/include',
            'AR999A_ArchGlbPrm_Impl/include',
            'ES999A_ElecGlbPrm_Impl/include',
            'SF999A_SysGlbPrm_Impl/include'
        )
        
        # set stub file paths
        stub_c_path = os.path.join(self.local_generate_dir, 'Rte_Stubs.c').replace('\\', '/')
        stub_h_path = os.path.join(self.local_generate_dir, 'Rte_Stubs.h').replace('\\', '/')
        stub_math_path = os.path.join(self.local_generate_dir, 'math_stubs.h').replace('\\', '/')
        #globals_path = os.path.join(self.local_generate_dir, 'CDD_MotCtrlMgr_Data.h').replace('\\', '/')
        
        # get source files
        search_dirs = []
        search_dirs.append(self.src_dir)
        search_dirs.append(self.local_generate_dir)
        search_dirs.append(self.local_src_dir)
        
        source_paths = []
        for dir in search_dirs:
            if not os.path.exists(dir):
                continue
            for file in os.listdir(dir):
                if file.endswith('.c'):
                    source_paths.append(os.path.join(dir, file).replace('\\', '/'))
        
        if dd_path and stub_c_path not in source_paths:
            source_paths.append(stub_c_path)
        
        # set up include paths
        include_dirs = []
        include_dirs.append(self.include_dir.replace('\\', '/'))
        include_dirs.append(self.local_generate_dir.replace('\\', '/'))
        include_dirs.append(self.local_include_dir.replace('\\', '/'))
        for include in standard_includes:
            include_dirs.append(os.path.join(parent_dir, include).replace('\\', '/'))
        include_dirs.append('C:/ghs/comp_201517/include/v800')
        
        # set up ignore paths
        ignores = []
        for include in standard_includes:
            ignores.append(os.path.join(parent_dir, include).replace('\\', '/'))
        ignores.append('C:/ghs/comp_201517/include/v800')
        
        # collect template names (don't ignore local files created from templates)
        templates = []
        if os.path.exists(self._template_dir):
            for file in os.listdir(self._template_dir):
                if file.endswith('.tt'):
                    templates.append(file[:-3])
                elif '_template' in file.lower():
                    idx = file.lower().index('_template')
                    templates.append(file[:idx] + file[idx+9:])
                elif file.endswith('.c') or file.endswith('.h'):
                    templates.append(file)
        
        # check local directories for files to ignore
        check_dirs = []
        check_dirs.append(self.local_generate_dir)
        check_dirs.append(self.local_include_dir)
        check_dirs.append(self.local_src_dir)
        
        for dir in check_dirs:
            if os.path.exists(dir):
                for file in os.listdir(dir):
                    if file.endswith('.c') or file.endswith('.h'):
                        if file not in templates:
                            ignores.append(os.path.join(dir, file).replace('\\', '/'))
        
        # add stub files if not already added
        if dd_path:
            if stub_c_path not in ignores:
                ignores.append(stub_c_path)
            if stub_h_path not in ignores:
                ignores.append(stub_h_path)
            if stub_math_path not in ignores:
                ignores.append(stub_math_path)
            #if globals_path not in ignores:
                #ignores.append(globals_path)
        
        # use a DRS file in CodeProver?
        use_drs = True if dd_path else False
        
        # set polyspace path for templates
        polyspace_dir = self.polyspace_dir.replace('\\', '/')
        generate_dir = self.local_generate_dir.replace('\\', '/')
        
        # render codeprover project file from template
        codeprover_template = mako.template.Template(filename=_codeprover_template_file)
        codeprover_rendered = codeprover_template.render(polyspace_dir=polyspace_dir, include_dirs=include_dirs, source_paths=source_paths, ignores=ignores, use_drs=use_drs).replace('\r', '')
        
        # update codeprover project file
        files_changed |= nxtr.write_if_changed(codeprover_rendered, self.codeprover_path)
        
        # render bugfinder project file from template
        bugfinder_template = mako.template.Template(filename=_bugfinder_template_file)
        bugfinder_rendered = bugfinder_template.render(polyspace_dir=polyspace_dir, include_dirs=include_dirs, source_paths=source_paths, ignores=ignores).replace('\r', '')
        
        # update bugfinder project file
        files_changed |= nxtr.write_if_changed(bugfinder_rendered, self.bugfinder_path)
        
        # copy MISRA settings configuration file
        misra_config_path = os.path.join(self.polyspace_dir, 'MISRASettings.cfg')
        files_changed |= nxtr.copy_if_changed(_misra_template_file, misra_config_path)
        
        # copy math_stubs.h project file
        math_stubs_path = os.path.join(self.local_generate_dir, 'math_stubs.h')
        files_changed |= nxtr.copy_if_changed(_math_stubs_template_file, math_stubs_path)
        
        # if data dictionary provided, create stub files
        if dd_path:
            
            # parse data dictionary
            dd_objs = datadict.parse_data_dict(dd_path)
            
            # open RTE header file
            header = None
            header_file = 'Rte_' + self.short_name + '.h'
            header_path = os.path.join(self.local_generate_dir, header_file)
            if not os.path.exists(header_path):
                header_file = 'Rte_CDD_' + self.short_name + '.h'
                header_path = os.path.join(self.local_generate_dir, header_file)
                if not os.path.exists(header_path):
                    header_file = None
                    header_path = None
            
            # read RTE header for later use
            if header_path:
                with open(header_path, 'r') as file:
                    header = file.read()
                include_tag = '\n#include "Rte_Stubs.h"\n'
                if not header.endswith(include_tag):
                    with open(header_path, 'a') as file:
                        file.write(include_tag)
                        files_changed = True
            
            # get DRS statements
            drs = []
            for dd_obj in dd_objs:
                
                # check for client/server port objects
                if dd_obj.value == 'DataDict.Client' or dd_obj.value == 'DataDict.SrvRunnable':
                    
                    # ignore fault injection ports
                    if 'FltInj_' in dd_obj.name:
                        continue
                    
                    # set name and symbol prefix
                    if dd_obj.value == 'DataDict.Client':
                        name = self.short_name + '_' + dd_obj.name
                        prefix = '_Srv_'
                    else:
                        name = dd_obj.name
                        prefix = '_Cli_'
                    
                    # if port name not found in RTE header, skip this object
                    if _check_header(header, name) is None:
                        continue
                    
                    # get DRS statements for return value and arguments
                    for sub_obj in dd_obj.children:
                        if sub_obj.value == 'DataDict.CSArguments' or sub_obj.value == 'DataDict.CSReturn':
                            drs.extend(sub_obj.get_drs(''.join([self.short_name, prefix, dd_obj.name])))
                
                # check for other DRS objects
                else:
                    suffix = _ps_stub_suffix(dd_obj)
                    
                    if suffix:
                        drs.extend(dd_obj.get_drs(self.short_name + suffix))
            
            # additional DRS statements for math.h stubs
            drs.append('sqrtf.return 0 max permanent')
            drs.append('fmodf.return 0 max permanent')
            drs.append('expf.return 0 max permanent')
            drs.append('sinf.return -1 1 permanent')
            drs.append('cosf.return -1 1 permanent')
            drs.append('atan2f.return -3.1412 3.1412 permanent')
            
            # write DRS file
            drs_path = os.path.join(self.polyspace_dir, 'DRS.txt')
            files_changed |= nxtr.write_if_changed('\n'.join(drs), drs_path)
            
            # collect stub objects
            stubs = {}
            stubs['ip'] = []
            stubs['op'] = []
            stubs['cal'] = []
            stubs['pim'] = []
            stubs['irv'] = []
            servers = []
            clients = []
            globals = []
            
            for dd_obj in dd_objs:
                
                # check for runnable objects
                if dd_obj.value == 'DataDict.Runnable':
                    
                    name = dd_obj.name
                    
                    if header is not None and name not in header:
                        # check context for NonRte
                        non_rte = False
                        for obj in dd_obj.children:
                            if obj.name == 'Context':
                                if obj.value == '\'NonRte\'':
                                    non_rte = True
                        if not non_rte:
                            continue
                    
                    clients.append({'name': name, 'return': None, 'args': []})
                
                # check for client/server port objects
                elif dd_obj.value == 'DataDict.Client' or dd_obj.value == 'DataDict.SrvRunnable':
                    
                    # ignore fault injection ports
                    if 'FltInj_' in dd_obj.name:
                        continue
                    
                    # set name and symbol prefix
                    if dd_obj.value == 'DataDict.Client':
                        name = self.short_name + '_' + dd_obj.name
                        prefix = '_Srv_'
                    else:
                        name = dd_obj.name
                        prefix = '_Cli_'
                    
                    # get actual RTE name from RTE header file - if not found, skip
                    name = _check_header(header, name)
                    if name is None:
                        continue
                    
                    # get arguments and return objects for this port
                    args = []
                    ret = None
                    for sub_obj in dd_obj.children:
                        if sub_obj.value == 'DataDict.CSArguments' or sub_obj.value == 'DataDict.CSReturn':
                            stub_obj = sub_obj.get_rte_stub(''.join([self.short_name, prefix, dd_obj.name]))
                            if stub_obj:
                                if sub_obj.value == 'DataDict.CSArguments':
                                    args.append(stub_obj)
                                else:
                                    ret = stub_obj
                    
                    # add to client/server list
                    if dd_obj.value == 'DataDict.Client':
                        servers.append({'name': name, 'return': ret, 'args': args})
                    else:
                        clients.append({'name': name, 'return': ret, 'args': args})
                
                # check for other stub objects
                else:
                    suffix = _ps_stub_suffix(dd_obj)
                    
                    if suffix:
                        stub_obj = dd_obj.get_rte_stub(self.short_name + suffix)
                        
                        # if object needs a stub, add to appropriate list
                        if stub_obj:
                            if stub_obj['rte_name'] is None:
                                globals.append(stub_obj)
                            elif dd_obj.value == 'DataDict.IpSignal':
                                stubs['ip'].append(stub_obj)
                            elif dd_obj.value == 'DataDict.OpSignal':
                                stubs['op'].append(stub_obj)
                            elif dd_obj.value == 'DataDict.Calibration' or dd_obj.value == 'DataDict.ImprtdCal':
                                stubs['cal'].append(stub_obj)
                            elif dd_obj.value == 'DataDict.PIM' or dd_obj.value == 'DataDict.NVM' or dd_obj.value == 'DataDict.Display':
                                stubs['pim'].append(stub_obj)
                            elif dd_obj.value == 'DataDict.IRV':
                                stubs['irv'].append(stub_obj)
            
            # render RTE stub files from template
            stub_c_template = mako.template.Template(filename=_stub_c_template_file)
            stub_h_template = mako.template.Template(filename=_stub_h_template_file)
            stub_c_rendered = stub_c_template.render(rte_header=header_file, servers=servers, clients=clients, irvs=stubs['irv']).replace('\r', '')
            stub_h_rendered = stub_h_template.render(stubs=stubs, servers=servers, clients=clients, comp_num = self.comp_num).replace('\r', '')
            
            # write RTE stub files
            stub_c_path = os.path.join(self.local_generate_dir, 'Rte_Stubs.c')
            stub_h_path = os.path.join(self.local_generate_dir, 'Rte_Stubs.h')
            files_changed |= nxtr.write_if_changed(stub_c_rendered, stub_c_path)
            files_changed |= nxtr.write_if_changed(stub_h_rendered, stub_h_path)     
            
            # render and write MotCtrl stub file if necessary
            #if globals:
            #    globals_template = mako.template.Template(filename=_globals_template_file)
            #    globals_rendered = globals_template.render(rte_header=header_file, globals=globals).replace('\r', '')
            #    globals_path = os.path.join(self.local_generate_dir, 'CDD_MotCtrlMgr_Data.h')
            #    files_changed |= nxtr.write_if_changed(globals_rendered, globals_path)
        
        # return response message
        if files_changed:
            msg = 'The Polyspace files were updated successfully.'
        else:
            msg = 'The Polyspace files are already up to date.'
        if not dd_path:
            msg += '\n\nNo Data Dictionary was available, so CodeProver results may be inaccurate.'
        return 0, msg