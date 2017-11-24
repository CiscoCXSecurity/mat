# python modules
from subprocess import Popen, PIPE
from os import path
import traceback

from time import sleep
from uuid import uuid4

# local imports
from utils import Utils, Log, Command
import settings

################################################################################
#    IOS UTILS FUNCTIONS
################################################################################

class IOSUtils(object):

    KEYCHAIN_DUMP     = None
    DUMP_FILE_PROTECT = None
    DUMP_LOG          = None
    DUMP_DECRYPT      = None

    def __init__(self):
        self.CHECKS_PASSED = {}
        self.launched      = False
        if not settings.static:
            self.start_tcp_relay()

    def launch_app(self, app_info):
        if not self.launched:
            Log.w('Starting the application on the device')
            self.launched = True
            self.run_app(app_info)
            sleep(5)

    def clean(self):
        self.stop_tcp_relay()

    def run_on_ios(self, cmd='', shell=False, process=False, timeout=5, retry=2):
        Log.d('Running on iOS: {cmd}'.format(cmd=cmd))

        try:
            cmd = cmd.replace("\ ", " ") # fix for backslashes
            full_cmd = '{ssh} \'{cmd}\''.format(ssh=settings.ssh_ios, cmd=cmd) if shell else [settings.ssh_ios, cmd]
            Log.d('Full command: {cmd}'.format(cmd=full_cmd))

            if process:
                return Popen(full_cmd, stdout=PIPE, stderr=None, shell=shell)

            result = Command(full_cmd).run(shell, timeout)
            if result:
                result = (result[0].split('\r\n', 2)[2], result[1]) if 'password:' in result[0] else (result[0].split('\r\n', 1)[1], result[1])

            if 'ssh_exchange_identification: Connection closed by remote host' in result[0] and retry > 0:
                return self.run_on_ios(cmd, shell, process, timeout, retry-1)

            return result
        except Exception:
            Log.d(traceback.format_exc())

        if retry > 0:
            return self.run_on_ios(cmd, shell, process, timeout, retry-1)

        return ['', '']

    def run_app(self, app_info):
        return self.run_on_ios('open {app}'.format(app=app_info['CFBundleIdentifier']))

    def flags(self, ios_app_bin, local_app_bin):
        if settings.otool:
            return Utils.run('{otool} -hv "{app}"'.format(otool=settings.otool, app=local_app_bin), shell=True)[0]
        elif self.check_dependencies(['connection'], silent=True, install=False):
            return self.run_on_ios('otool -hv {app}'.format(app=ios_app_bin))[0]
        return ''

    def dump_otool_classes(self, result):
        found_classes = []
        parsing = method_name = parsed_property = ''
        parsed_class = {}
        meta = False
        for line in result.split('\n'):
            if 'Meta Class' in line:
                meta = True

            if meta and 'baseProperties 0x0' in line:
                method_name = parsed_property = ''

                if 'name' in parsed_class:
                    found_classes += [parsed_class]
                parsed_class = {}
                meta = False

            elif '_OBJC_CLASS_' in line:
                parsed_class['name'] = line.rsplit('$', 1)[-1].strip()[1:]
                parsing = 'class'
            elif 'struct class_ro_t' in line:
                parsing = 'class'
            elif parsing == 'class' and 'name' in line:
                parsed_class['name'] = line.strip().rsplit(' ', 1)[-1].strip()

            elif parsing == 'base_properties' and parsed_property and 'attributes' in line:
                ptype, attrs = self.dump_attributes_property(line)
                parsed_class['base_properties'] += ['@property{attrs} {type} {name};'.format(attrs=attrs, type=ptype, name=parsed_property)]
                parsed_property = ''
            elif parsing == 'base_properties' and 'name' in line:
                parsed_property = line.strip().rsplit(' ', 1)[-1]
            elif 'baseProperties' in line:
                parsing = 'base_properties'
                if 'base_properties' not in parsed_class: parsed_class['base_properties'] = []

            elif parsing == 'instance_properties' and parsed_property and 'type' in line:
                ptype = line.strip().rsplit(' ', 1)[-1]
                parsed_class['instance_properties'] += ['{t} {n};'.format(t=self.dump_attr_type(ptype), n=parsed_property)]
                parsed_property = ''
            elif parsing == 'instance_properties' and 'name' in line:
                parsed_property = line.strip().rsplit(' ', 1)[-1]
            elif 'instanceProperties' in line:
                parsing = 'instance_properties'
                if 'instance_properties' not in parsed_class: parsed_class['instance_properties'] = []

            elif parsing == 'instance_methods' and method_name and 'types' in line:
                types = self.dump_class_types(line.strip().split(' ', 2)[-1])
                parsed_class['instance_methods'] += ['+ ({rvalue}){name};'.format(rvalue=types[0], name=self.dump_method_name(method_name, types[1:]))]
                method_name = ''
            elif parsing == 'instance_methods' and 'name' in line:
                method_name = line.strip().rsplit(' ', 1)[-1]
            elif 'instanceMethods' in line:
                if 'instance_methods' not in parsed_class: parsed_class['instance_methods'] = []
                parsing = 'instance_methods'

            elif parsing == 'protocols' and parsed_property and 'type' in line:
                ptype = line.strip().rsplit(' ', 1)[-1]
                parsed_class['protocols'] += ['{t} {n};'.format(t=self.dump_attr_type(ptype), n=parsed_property)]
                parsed_property = ''
            elif parsing == 'protocols' and 'name' in line:
                parsed_property = line.strip().rsplit(' ', 1)[-1]
            elif 'baseProtocols' in line:
                parsing = 'protocols'
                if 'protocols' not in parsed_class: parsed_class['protocols'] = []

            elif parsing == 'methods' and method_name and 'types' in line:
                types = self.dump_class_types(line.strip().split(' ', 2)[-1])
                parsed_class['methods'] += ['- ({rvalue}){name};'.format(rvalue=types[0], name=self.dump_method_name(method_name, types[1:]))]
                method_name = ''
            elif parsing == 'methods' and 'name' in line:
                method_name = line.strip().rsplit(' ', 1)[-1]
            elif 'baseMethods' in line:
                if 'methods' not in parsed_class: parsed_class['methods'] = []
                parsing = 'methods'

            elif 'Contents of' in line and not "Contents of (__DATA,__objc_classlist) section" in line:
                break

        """
        for a in c:
            print "//\n//    Generated by MAT v1.0.0\n//\n//    {name}\n//\n\n// attributes\n".format(name=a['name'])
            print '\n'.join(a['protocols']) if 'protocols' in a else ''
            print '\n// instance properties\n'
            print '\n'.join(a['instance_properties']) if 'instance_properties' in a else ''
            print '\n// base properties\n'
            print '\n'.join(a['base_properties']) if 'base_properties' in a else ''
            print '\n// methods\n'
            print '\n'.join(a['methods']) if 'methods' in a else ''
        """

        return found_classes

    def dump_jtool_classes(self, result):
        #/usr/local/bin/jtool -v -d objc -arch armv7 /tmp/MB
        found_classes = []
        parsed_class = {}
        parsing = ''
        for line in result.split('\n'):
            if '(null)' in line:
                continue

            if '@end' in line:
                found_classes += [parsed_class]
                parsed_class = {}
                parsing = ''

            elif 'Dumping class' in line:
                parsing = 'class'
                parsed_class['name'] = line.split('(', 1)[-1].replace(')', '')

            elif 'properties' in line and '//' in line:
                parsing = 'properties'
            elif 'instance variables' in line and '//' in line:
                parsing = 'instance_variables'
                parsed_class['instance_properties'] = []
            elif parsing == 'instance_variables' and '/*' in line:
                name = line.split(';', 1)[0].rsplit(' ', 1)[-1].replace('*', '')
                ptype = line.rsplit('// ', 1)[-1]
                parsed_class['instance_properties'] += ['{t} {n};'.format(t=self.dump_attr_type(ptype), n=name)]

            elif 'instance methods' in line and '//' in line:
                parsing = 'methods'
                parsed_class['methods'] = []
            elif parsing == 'methods' and '/*' in line:
                types = self.dump_class_types(line.rsplit('Protocol ', 1)[-1])
                method_name = line.rsplit(' - ', 1)[-1].rsplit(';', 1)[0]
                parsed_class['methods'] += ['- ({rvalue}){name};'.format(rvalue=types[0], name=self.dump_method_name(method_name, types[1:]))]

        return found_classes

    def dump_class_types(self, string):
        types = {
            'v': 'void', 'f': 'float', 'S': 'short', 's': 'short',
            'I': 'unsigned int', 'i': 'long long', 'd': 'double', 'B': 'Bool',
            'l': 'long', 'L': 'long', 'c': 'Bool', 'Q': 'Bool', '@': 'id',
            '.': 'UnknownType', '#': 'Class', '*': 'char * ', ':': 'SEL',
            'C': 'unsigned char', 'q': 'long long'
        }

        ntypes = []
        ignore = 0
        saved_type = ''
        for i in string.replace('@0:', '').replace('@?', '.').replace('^?', '.'):

            if '{' in i:
                ignore += 1
                if ignore == 1:
                    saved_type = '_'
            elif '=' in i and saved_type:
                ntypes += ['struct {t}'.format(t=saved_type[1:])]
                saved_type = ''
            elif saved_type and ignore > 0:
                saved_type += i
            elif '}' in i:
                ignore -= 1
            elif i in types and ignore == 0:
                ntypes += [types[i]]

        return ntypes

    def dump_method_name(self, name, types):
        if len(types) == 0:
            return name.replace(':', '')

        # TODO: needs fixing -> just hammering mistakes
        while name.count(':') > len(types):
            types += ['void']

        return ' '.join(['{n}:({t})arg{i}'.format(n=a, t=types[i], i=(i+1)) for i, a in enumerate(name.split(':')[:-1])])

    def dump_attr_type(self, string):
        if string[0] == 'T':
            string = string[1:]

        if string.startswith('@"'):
            return '{n} *'.format(n=string.split('"')[-2])

        types = self.dump_class_types(string)
        return types[0] if len(types) > 0 else "id"

    def dump_attributes_property(self, attrs):
        attributes = {'N': 'nonantomic', 'R': 'readonly', 'C': 'copy', '&': 'retain'}
        attrs = attrs.rsplit(' ', 1)[-1].split(',')
        return self.dump_attr_type(attrs[0]), '({attrs}){weak}'.format(weak=' __weak' if 'W' in attrs else '', attrs=', '.join([attributes[a] for a in attrs[1:] if a in attributes]))

    def dump_classes(self, local_app_bin):
        result = Utils.run('{otool} -ov "{app}"'.format(otool=settings.otool, app=local_app_bin), shell=True)[0]
        return self.dump_jtool_classes(result) if 'Dumping class' in result else self.dump_otool_classes(result)

    def dump_classes_to_file(self, classes, rootpath):
        for a in classes:
            with open('{path}/{name}.h'.format(path=rootpath, name=a['name']), 'w') as f:
                f.write("//\n//    Generated by MAT v{version}\n//\n//    {name}\n//\n\n// attributes\n".format(name=a['name'], version=settings._VERSION))
                f.write('\n'.join(a['protocols']) if 'protocols' in a else '')
                f.write('\n\n// instance properties\n')
                f.write('\n'.join(a['instance_properties']) if 'instance_properties' in a else '')
                f.write('\n\n// base properties\n')
                f.write('\n'.join(a['base_properties']) if 'base_properties' in a else '')
                f.write('\n\n// methods\n')
                f.write('\n'.join(a['methods']) if 'methods' in a else '')
                f.write('\n\n// instance methods\n')
                f.write('\n'.join(a['instance_methods']) if 'instance_methods' in a else '')

    def symbols(self, ios_app_bin, local_app_bin):
        if settings.otool:
            return Utils.run('{otool} -Iv "{app}"'.format(otool=settings.otool, app=local_app_bin), shell=True)[0]
        elif self.check_dependencies(['connection'], silent=True, install=False):
            return self.run_on_ios('otool -Iv {app}'.format(app=ios_app_bin))[0]
        return ''

    def dump_keychain(self, dest='/tmp'):
        dest = dest.replace('\ ', ' ')
        if self.KEYCHAIN_DUMP:
            Log.d('Dumping Keychain data to {dest} with {bin}'.format(bin=self.KEYCHAIN_DUMP, dest=dest))
            self.run_on_ios('cd "{working}"; {keychain}'.format(working=dest, keychain=self.KEYCHAIN_DUMP), shell=True)
        else:
            Log.d('Error: No keychain dump binary found - was prepare_analysis run?')

    def dump_file_protect(self, file):
        file = file.replace('\ ', ' ')
        if self.DUMP_FILE_PROTECT:
            Log.d('Dumping file protection flags of {file} with {bin}'.format(bin=self.DUMP_FILE_PROTECT, file=file))
            return self.run_on_ios('{dfp} "{file}"'.format(dfp=self.DUMP_FILE_PROTECT, file=file), shell=True)[0]
        else:
            Log.d('Error: No file protection dump binary found - was prepare_analysis run?')

    def dump_log(self, app):
        if self.DUMP_LOG:
            Log.d('Dumping logs of {app} with {bin}'.format(bin=self.DUMP_LOG, app=app))
            return self.run_on_ios('{dumplog} {app}'.format(dumplog=self.DUMP_LOG, app=app))[0]
        else:
            Log.d('Error: No dumplog binary found - was prepare_analysis run?')

    def dump_backup_flag(self, file):
        if self.BACKUP_EXCLUDED:
            Log.d('Dumping backup flag of {file} with {bin}'.format(bin=self.BACKUP_EXCLUDED, file=file))
            return self.run_on_ios('{dbf} "{file}"'.format(dbf=self.BACKUP_EXCLUDED, file=file), shell=True)[0]
        else:
            Log.d('Error: No backup_excluded binary found - was prepare_analysis run?')

    def apt_install(self, package):
        return self.run_on_ios('apt-get -y install {package}'.format(package=package))

    def set_proxy(self, ip=None, port=None):
        Log.d("Adding proxy {ip}:{port}".format(ip=ip, port=port))
        PREF_FILE = '/private/var/preferences/SystemConfiguration/preferences.plist'

        prefs = self.get_plist(PREF_FILE)

        current = prefs['CurrentSet'].rsplit('/', 1)[1]
        currentServices = prefs['Sets'][current]['Network']['Global']['IPv4']['ServiceOrder']

        for currentService in currentServices:
            if 'IPv4' in prefs['NetworkServices'][currentService]:
                break

        service = None
        for existingService in prefs['NetworkServices']:
            if 'IPv4' in prefs['NetworkServices'][existingService]:

                if not ip or not port and not 'HTTPEnable' in prefs['NetworkServices'][existingService]['Proxies']:
                    service = existingService
                    break
                elif ip and port and 'HTTPProxy' in prefs['NetworkServices'][existingService]['Proxies'] and prefs['NetworkServices'][existingService]['Proxies']['HTTPProxy'] == ip and prefs['NetworkServices'][existingService]['Proxies']['HTTPPort'] == port:
                    service = existingService
                    break

        Log.d("Changing service from {cs} to {es}".format(cs=currentService, es=service))
        if not service:
            service = str(uuid4())
            serviceObject = {
                'DNS': {},
                'IPv4': {
                    'ConfigMethod': 'DHCP'
                },
                'IPv6': {
                    'ConfigMethod': 'Automatic'
                },
                'Interface': {
                    'DeviceName': 'en0',
                    'Hardware': 'AirPort',
                    'Type': 'Ethernet',
                    'UserDefinedName': 'Wi-Fi'
               },
                'Proxies': {
                    'ExceptionsList': ['*.local', '169.254/16'],
                    'FTPPassive': 1,
                    'HTTPEnable': 1,
                    'HTTPPort': port,
                    'HTTPProxy': ip,
                    'HTTPSEnable': 1,
                    'HTTPSPort': port,
                    'HTTPSProxy': ip
                },
                'UserDefinedName': 'Wi-Fi'
            }
            prefs['NetworkServices'][service] = serviceObject

        prefs['Sets'][current]['Network']['Global']['IPv4']['ServiceOrder'].remove(currentService)
        prefs['Sets'][current]['Network']['Global']['IPv4']['ServiceOrder'] += [service]

        prefs['Sets'][current]['Network']['Service'].pop(currentService)
        prefs['Sets'][current]['Network']['Service'][service] = {'__LINK__': '/NetworkServices/{service}'.format(service=service)}

        Log.d("Writing preference file")
        with open('/tmp/preferences.plist', 'w') as f:
            f.write(self.dict_to_plist(prefs))
        self.push('/tmp/preferences.plist', PREF_FILE.rsplit('/', 1)[0])
        self.plist_to_bin(PREF_FILE)

        if self.check_dependencies(['proxy'], install=True):
            self.run_on_ios('activator send switch-off.com.a3tweaks.switch.wifi')
            self.run_on_ios('activator send switch-on.com.a3tweaks.switch.wifi')
            return True

        Log.d('Activator not found in the device. Please turn the WiFi off and on again manually')

    def check_dependencies(self, dependencies=['full'], silent=False, install=False, force=False):
        Log.d('Checking dependencies: {dep}'.format(dep=dependencies))

        ########################################################################
        # CHECK PRE REQUESITES
        ########################################################################
        if not isinstance(dependencies, list):
            Log.d('Error: Dependencies must be a list')
            return False

        valid_dependencies   = ['full', 'connection', 'static', 'install', 'proxy', 'dynamic']
        invalid_dependencies = list(set(dependencies)-set(valid_dependencies))
        if invalid_dependencies:
            Log.d('Error: The following dependencies cannot be checked: {deps}'.format(deps=', '.join(invalid_dependencies)))
            return False

        ########################################################################
        # CHECK SAVED DEPENDENCIES
        ########################################################################
        if all([d in self.CHECKS_PASSED for d in dependencies]) and not force: # if all dependencies have been checked before
            return all([self.CHECKS_PASSED[d] for d in self.CHECKS_PASSED if d in dependencies])

        if 'full' in dependencies:
            self.CHECKS_PASSED['full'] = True

        ########################################################################
        # CONNECTION DEPENDENCIES
        ########################################################################

        if 'full' in dependencies or 'connection' in dependencies:
            self.CHECKS_PASSED['connection'] = True

            connection_dependencies = ['expect']
            for d in connection_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['connection'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

            uname = self.run_on_ios('uname -m')[0].lower()
            if 'Connection refused' in uname or 'Connection closed' in uname:
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['connection'] = False

            if 'iphone' not in uname and 'ipad' not in uname and 'ipod' not in uname:
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['connection'] = False
            if not silent: Log.w('device check: {connected}'.format(connected=uname.strip()))

            required_packages  = ['apt7', 'coreutils', 'com.conradkramer.open', 'com.ericasadun.utilities', 'odcctools']
            installed_packages = self.installed_packages()
            not_installed      = set(required_packages) - set(installed_packages)
            if not_installed:
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['connection'] = False
            if not silent: Log.w('packages installed: {packages}'.format(packages=', '.join(list(set(required_packages) - not_installed))))
            if not silent and not_installed: Log.w('packages missing: {packages}'.format(packages=', '.join(list(not_installed))))

        if 'full' in dependencies or 'dynamic' in dependencies:
            self.CHECKS_PASSED['dynamic'] = True

            if 'connection' in self.CHECKS_PASSED and not self.CHECKS_PASSED['connection'] and 'Darwin' not in Utils.run('uname')[0]:
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['dynamic'] = False

            if 'Darwin' not in Utils.run('uname')[0]:
                if install and not self.run_on_ios('which Clutch2')[0][:-2]:
                    if not silent: Log.w('Trying to install missing tools')
                    self.apt_install('curl')
                    self.run_on_ios('curl -ksL "http://cydia.iphonecake.com/Clutch2.0.4.deb" -o /tmp/kill.deb')
                    self.run_on_ios('dpkg -i /tmp/kill.deb && rm -f /tmp/kill.deb')
                    self.run_on_ios('killall -HUP SpringBoard')
                    self.run_on_ios('chmod +x /usr/bin/Clutch2')

                clutch = self.run_on_ios('which Clutch2')[0][:-2]
                if not clutch:
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['dynamic'] = False
                if not silent: Log.w('iOS clutch2: {path}'.format(path=clutch.strip()))

        ########################################################################
        # STATIC DEPENDENCIES
        ########################################################################

        if 'full' in dependencies or 'static' in dependencies:
            self.CHECKS_PASSED['static'] = True

            static_dependencies = ['plutil']
            for d in static_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['static'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

        ########################################################################
        # INSTALL DEPENDENCIES
        ########################################################################

        if 'full' in dependencies or 'install' in dependencies:
            self.CHECKS_PASSED['install'] = True

            if install and not self.run_on_ios('which ipainstaller')[0][:-2]:
                if not silent: Log.w('Trying to install missing tools')
                self.apt_install('com.slugrail.ipainstaller')

            ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]
            if not ipainstaller:
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['install'] = False

            if not silent: Log.w('iOS ipainstaller: {path}'.format(path=ipainstaller.strip()))

        ########################################################################
        # PROXY DEPENDENCIES - NOT PART OF FULL CHECK
        ########################################################################

        if 'proxy' in dependencies:
            self.CHECKS_PASSED['proxy'] = True

            if install and not self.run_on_ios('which activator')[0][:-2]:
                if not silent: Log.w('Trying to install missing tools')
                self.apt_install('libactivator')

            activator = self.run_on_ios('which activator')[0][:-2]
            if not activator:
                self.CHECKS_PASSED['proxy'] = False

            if not silent: Log.w('iOS activator: {path}'.format(path=activator.strip()))

            required_packages  = ['com.ericasadun.utilities', 'libactivator']
            installed_packages = self.installed_packages()
            not_installed      = set(required_packages) - set(installed_packages)
            if not_installed:
                self.CHECKS_PASSED['proxy'] = False
            if not silent: Log.w('packages installed: {packages}'.format(packages=', '.join(list(set(required_packages) - not_installed))))
            if not silent and not_installed: Log.w('packages missing: {packages}'.format(packages=', '.join(list(not_installed))))


        return all([self.CHECKS_PASSED[d] for d in self.CHECKS_PASSED if d in dependencies])

    def installed_packages(self):
        return [line.split(' ')[2] for line in self.run_on_ios('dpkg -l')[0].split('\n') if 'iphoneos-arm' in line]

    def install(self, ipa):
        if not self.check_dependencies(['connection', 'install'], install=True):
            Log.d('Error: No IPA Installer installed on the device')
            return False

        if not path.exists(ipa) or not path.isfile(ipa):
            Log.d('Error: Invalid IPA file')
            return False

        tmp_folder = '/tmp/ipa-{uuid}'.format(uuid=uuid4())
        app_path, app_info = self.unzip_to(ipa=ipa, dest=tmp_folder)
        apps = self.list_apps(silent=True)
        app  = [a for a in apps if app_path.rsplit('/', 1)[-1].lower() in apps[a]['Path'].lower()]

        # install the app
        if (app and 'Version' in apps[app[0]] and apps[app[0]]['Version'] < app_info['CFBundleVersion']) or not app or not 'Version' in apps[app[0]]:
            self.push(ipa, '/tmp')
            settings.ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]

            name = ipa.rsplit('/', 1)[1] if '/' in ipa else ipa
            name = name.replace('\ ', ' ')
            result = self.run_on_ios('{ipai} -f -d "/tmp/{ipa}"'.format(ipai=settings.ipainstaller, ipa=name), shell=True)[0]

            if 'Failed' in result or 'Invalid' in result:
                Log.e('Error: Failed to install the IPA: {result}'.format(result=result.split('\r\n')[-2:-1][0]))
                return False

            Log.w('Waiting 10 seconds for the app to finish installing')
            sleep(10)
            self.update_apps_list(False)

            apps = self.list_apps(silent=True)
            app  = [a for a in apps if app_path.rsplit('/', 1)[-1].lower() in apps[a]['Path'].lower()]
            if not app:
                Log.d('Error: Couldn\'t find the installed app, try again')

        Utils.run('rm -rf {dest}'.format(dest=tmp_folder))

        return apps[app[0]] if app else None

    def unzip_to(self, ipa, dest):
        ipa, dest = ipa.replace('\ ', ' '), dest.replace('\ ', ' ')
        Utils.run('{unzip} -o "{ipa}" -d "{dest}"'.format(unzip=settings.unzip, ipa=ipa, dest=dest), shell=True)

        #from os import listdir
        #app = listdir('{dest}/Payload/'.format(dest=dest)).pop()
        files = Utils.run('{unzip} -l "{ipa}"'.format(unzip=settings.unzip, ipa=ipa), shell=True)[0].strip()
        import re
        app = re.search(r'Payload\/.*?\.app', files).group().split('/',1)[-1]

        self.plist_to_xml('{dest}/Payload/{app}/Info.plist'.format(dest=dest, app=app), ios=False)
        with open('{dest}/Payload/{app}/Info.plist'.format(dest=dest, app=app), 'r') as f:
            plist = f.read()

        return '{dest}/Payload/{app}'.format(dest=dest, app=app), self.plist_to_dict(plist)

    def app_executable(self, app, app_info):
        IOS_APP_BINARY        = app_info['CFBundleExecutable'].replace(' ', '\ ')
        IOS_APP_PATH          = app['Path'].replace(' ', '\ ')
        return '{apppath}/{appbin}'.format(apppath=IOS_APP_PATH, appbin=IOS_APP_BINARY)

    def pull_ipa(self, app, app_info, dest):
        Log.w('Pulling IPA')

        if not self.check_dependencies(['static', 'connection']):
            Log.d('Error: Dependencies not met - cannot pull the app')
            return False, False

        IOS_WORKING_BIN = IOS_IPA = None

        settings.ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]
        settings.clutch       = self.run_on_ios('which Clutch2')[0][:-2]

        # this needs to be here - do not use app_executable
        IOS_APP_BINARY        = app_info['CFBundleExecutable'].replace(' ', '\ ')
        IOS_APP_PATH          = app['Path'].replace(' ', '\ ')
        IOS_BINARY_PATH       = '{apppath}/{appbin}'.format(apppath=IOS_APP_PATH, appbin=IOS_APP_BINARY)

        # check if the app is encrypted and decrypt it
        if 'cryptid 1' in self.run_on_ios('otool -l "{binary}" | grep ENCRYPTION -B1 -A4'.format(binary=IOS_BINARY_PATH), shell=True)[0]:

            if self.DUMP_DECRYPT:
                self.run_on_ios('su mobile -c "cd {working}; DYLD_INSERT_LIBRARIES={dumpdecrypt} {binary}"'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, dumpdecrypt=self.DUMP_DECRYPT, binary=IOS_BINARY_PATH))

                # check if .decrypted file was created
                IOS_WORKING_BIN = '{working}/{binary}.decrypted'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=IOS_APP_BINARY)
                if not self.file_exists(self.IOS_WORKING_BIN):
                    Log.e("Error: Unable to decrypt app. Working with encrypted binary.")
                    self.IOS_WORKING_BIN = self.IOS_BINARY_PATH

            # Decrypt and Get the IPA file:
            Log.w('Decrypting the application to IPA. (this can take up to 30 secs)')
            result = self.run_on_ios('{clutch} -n -d {app}'.format(app=app['CodeInfoIdentifier'], clutch=settings.clutch), timeout=30)[0]
            if 'DONE:' in result:
                decryptedipa = result.split('DONE: ')[1].split('.ipa')[0]
                IOS_IPA = '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=IOS_APP_BINARY)
                self.run_on_ios('mv "{ipa}.ipa" "{newipa}"'.format(ipa=decryptedipa, newipa=IOS_IPA))

        if not IOS_IPA:
            Log.d('Application already decrypted')
            IOS_IPA= '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=IOS_APP_BINARY)
            self.run_on_ios('{installer} -b {app} -o "{ipa}"'.format(installer=settings.ipainstaller, app=app['CodeInfoIdentifier'], ipa=IOS_IPA))

        # get produced files
        Log.d('Getting binaries from device')
        LOCAL_WORKING_BIN = '{dest}/{binary}'.format(dest=dest, binary=IOS_WORKING_BIN.rsplit('/', 1)[-1])
        LOCAL_IPA         = '{dest}/{binary}'.format(dest=dest, binary=IOS_IPA.rsplit('/', 1)[-1])
        if IOS_WORKING_BIN: self.pull(IOS_WORKING_BIN, LOCAL_WORKING_BIN)
        if IOS_IPA: self.pull(IOS_IPA, LOCAL_IPA)

        return LOCAL_WORKING_BIN, LOCAL_IPA

    def plist_to_xml(self, file, ios=True):
        file = file.replace('\ ', ' ')
        if ios:
            self.run_on_ios('plutil -convert xml1 "{file}"'.format(file=file), shell=True)
        else:
            Utils.run('{plutil} -convert xml1 "{file}"'.format(plutil=settings.plutil, file=file), shell=True)

    def plist_to_bin(self, file, ios=True):
        file = file.replace('\ ', ' ')
        if ios:
            self.run_on_ios('plutil -convert binary1 "{file}"'.format(file=file), shell=True)
        else:
            Utils.run('{plutil} -convert binary1 "{file}"'.format(plutil=settings.plutil, file=file), shell=True)

    def delete(self, file):
        file = file.replace('\ ', ' ')
        self.run_on_ios('rm -rf "{file}"'.format(file=file), shell=True)
        return True

    def push(self, file, path):
        file, path = file.replace('\ ', ' '), path.replace('\ ', ' ')
        cmd = '{scp} "{file}" "{path}/{end}"'.format(scp=settings.scp_to_ios, file=file, path=path, end=file.split('/')[-1])
        results = Utils.run(cmd, shell=True)
        return '100%' in results[0]

    def read_file(self, file, ios=True):
        file = file.replace('\ ', ' ')
        if ios: return self.run_on_ios('cat "{file}"'.format(file=file), shell=True)[0]
        return Utils.run('cat "{file}"'.format(file=file), shell=True)[0]

    def update_apps_list(self, silent=False):
        if not silent: Log.w('Updating apps list on iOS: may take up to 30 seconds')
        self.run_on_ios('uicache', timeout=30)

    def list_apps(self, silent=False):
        PATHS = [
            '/var/mobile/Library/Caches/com.apple.mobile.installation.plist', # IOS7
            '/var/mobile/Library/MobileInstallation/LastLaunchServicesMap.plist', # IOS8
            '/private/var/installd/Library/MobileInstallation/LastLaunchServicesMap.plist' # IOS9
        ]

        for apps_file in PATHS:
            if self.file_exists(apps_file):
                text = self.read_file(apps_file)

                # check if plain text file
                if '<key>' not in text:
                    self.plist_to_xml(apps_file)
                    text = self.read_file(apps_file)

                apps = self.plist_to_dict(text)['User']
                if not silent:
                   for app in apps:
                        print('{app} :\n    APP: {bin}\n    DATA: {data}'.format(app=app, bin=apps[app]['Path'], data=apps[app]['Container']))
                return apps

        Log.d('Error: Device OS not supported - backporting to old methods')
        return self._list_apps_installer(silent)

    def _list_apps_installer(self, silent=False):
        if self.check_dependencies(['install'], install=True, silent=True):
            settings.ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]
            apps_packages = self.run_on_ios('{ipainstaller} -l'.format(ipainstaller=settings.ipainstaller))[0][:-2].split('\r\n')

            FOUND_APPS = {}
            for app in apps_packages:
                app_details = self.run_on_ios('{ipainstaller} -i {package}'.format(ipainstaller=settings.ipainstaller, package=app))[0][:-2].split('\r\n')
                DETAILS = app_id = {}
                for line in app_details:
                    key, value = line.split(': ', 1)
                    key  = key.replace('Application', 'Path').replace('Data', 'Container').replace('Identifier', 'CodeInfoIdentifier')
                    if 'CodeInfoIdentifier' in key:
                        app_id = value
                    DETAILS[key] = value
                if app_id:
                    FOUND_APPS[app_id] = DETAILS

            if not silent:
                for app in FOUND_APPS:
                    print('{app} :\n    APP: {bin}\n    DATA: {data}'.format(app=app, bin=FOUND_APPS[app]['Path'], data=FOUND_APPS[app]['Container']))

            return FOUND_APPS

        return self._list_apps_old(silent)

    def _list_apps_old(self, silent=False):
        FOUND_APPS = {}

        APP_PATHS  = {
            7:  '/var/mobile/Applications',
            8:  '/var/mobile/Containers/Bundle/Application',
            9:  '/var/containers/Bundle/Application',
            10: '/var/containers/Bundle/Application'
        }

        DATA_PATHS = {
            7:  '/var/mobile/Applications',
            8:  '/private/var/mobile/Containers/Data/Application',
            9:  '/private/var/mobile/Containers/Data/Application',
            10: '/private/var/mobile/Containers/Data/Application'
        }

        APPS_PATH = APP_PATHS[int(self.get_ios_version())]
        DATA_PATH = DATA_PATHS[int(self.get_ios_version())]

        apps  = self.run_on_ios('ls -d {appspath}/*/*.app'.format(appspath=APPS_PATH))[0]
        datas = self.run_on_ios('ls -d {datapath}/*/Library/Caches/Snapshots/*'.format(datapath=DATA_PATH))[0]

        if 'No such file or directory' not in apps:
            iosapps = apps.split('\r\n')[:-1]
            iosdata = datas.split('\r\n')[:-1]

            for app in iosapps:
                uuid, name  = app.replace(APPS_PATH, '')[1:].split('/')
                data        = [d for d in iosdata if name.split('.', 1)[0].lower() in d.lower()]
                identifier = data[0].rsplit('/', 1)[-1] if data else None

                if identifier:
                    FOUND_APPS[identifier] = {
                        'Path': '{paths}/{uuid}/{name}'.format(paths=APPS_PATH, uuid=uuid, name=name),
                        'Container': data[0].split('/Library')[0] if data else None,
                        'CodeInfoIdentifier': identifier
                    }
                    if not silent:
                        print('{app} :\n    APP: {bin}\n    DATA: {data}'.format(app=identifier, bin=FOUND_APPS[identifier]['Path'], data=FOUND_APPS[identifier]['Container']))

        return FOUND_APPS

    def get_ios_version(self):
        cmd = 'grep -A 1 "ProductVersion" /System/Library/CoreServices/SystemVersion.plist | tail -n 1 | cut -d">" -f2 | cut -d"<" -f1';
        result = self.run_on_ios(cmd)
        return float(result[0][:3]) if result else None

    def start_tcp_relay(self):
        if not hasattr(settings, 'iproxy_process'):
            if not path.exists('/var/run/usbmuxd.pid'):
                Utils.run('usbmuxd', shell=True)
                Log.w('Please press Trust on your device within the next 10 seconds. Unplug and plug back in if no Trust popup shows up.')
                sleep(10)
            settings.iproxy_process = Utils.run('{iproxy} 2222 22'.format(iproxy=settings.iproxy), shell=True, process=True)

    def stop_tcp_relay(self):
        if hasattr(settings, 'iproxy_process'):
            settings.iproxy_process.kill()

    def file_exists(self, file):
        file = file.replace('\ ', ' ')
        return 'cannot access' not in self.run_on_ios('ls "{file}"'.format(file=file), shell=True)[0]

    def get_plist(self, file, ios=True):
        try:
            self.plist_to_xml(file, ios=ios)
            return self.plist_to_dict(self.read_file(file, ios=ios))
        except Exception:
            Log.d('Error getting the plist {file}'.format(file=file))
            Log.d(traceback.format_exc())
            return {}

    def get_info(self, path=None, ios=True):
        return self.get_plist('{app}/Info.plist'.format(app=path.replace(' ', '\ ')), ios=ios)

    def get_entitlements(self, ios_binary_path, local_binary_path):

        if settings.ldid:
            text = Utils.run('{ldid} -e "{app}"'.format(ldid=settings.ldid, app=local_binary_path))[0]
        elif self.check_dependencies(['connection'], silent=True, install=False):
            binary = ios_binary_path.replace('\ ', ' ') # remove the escaped spaces
            text = self.run_on_ios('ldid -e "{app}"'.format(app=binary))[0]

        if text.count('</plist>') > 1:
            stext = text.replace('\r\n', '\n').split('\n')
            text = '\r\n'.join([i for i in stext[:len(stext)/2]])

        if not text:
            return {}

        return self.plist_to_dict(text)

    def pull(self, file=None, path=None):
        if not file or not path: return False
        file, path = file.replace('\ ', ' '), path.replace('\ ', ' ')
        cmd = '{scp} "{file}" "{path}"'.format(scp=settings.scp_from_ios, file=file, path=path)
        results = Utils.run(cmd, shell=True)
        return '100%' in results[0]

    def get_archs(self, binary=None):
        result = []
        if binary:
            binary = binary.replace('\ ', ' ')
            out = self.run_on_ios('otool -hv "{binary}"'.format(binary=binary), shell=True)[0]
            if out:
                for arch in out.split('\n')[3:]:
                    if not arch or not 'EXECUTE' in arch: continue
                    if "ARM64" in arch:
                        result += ['arm64']
                    elif "ARM" in arch and "V6" in arch:
                        result += ['armv6']
                    elif "ARM" in arch and "V7S" in arch.upper():
                        result += ['armv7s']
                    elif "ARM" in arch and "V7" in arch:
                        result += ['armv7']
                    else:
                        result += ['other']
                        Log.d('Other Arch found. Please check manually')

        return result

    def dict_to_plist(self, text):
        import plistlib
        return plistlib.writePlistToString(text)

    def plist_to_dict(self, text):
        import plistlib
        return plistlib.readPlistFromString(text)

    def dict_key_to_xml(self, plist, key):
        if key not in plist: return ''

        import plistlib
        xml = plistlib.writePlistToString({key: plist[key]})
        return '\n'.join(xml.split('\n')[3:-2])