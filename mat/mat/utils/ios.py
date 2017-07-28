# python modules
from subprocess import Popen, PIPE
from os import path
import traceback

# local imports
from utils import Utils, Log, Command, die
import settings

################################################################################
#    IOS UTILS FUNCTIONS
################################################################################

class IOSUtils(object):

    PREF_FILE         = '/private/var/preferences/SystemConfiguration/preferences.plist'
    KEYCHAIN_DUMP     = None
    DUMP_FILE_PROTECT = None
    DUMP_LOG          = None

    def run_on_ios(self, cmd='', shell=False, process=False, timeout=5):
        Log.d('Running on iOS: {cmd}'.format(cmd=cmd))

        try:
            cmd = '{ssh} \'{cmd}\''.format(ssh=settings.ssh_ios, cmd=cmd) if shell else [settings.ssh_ios, cmd]
            Log.d('Full command: {cmd}'.format(cmd=cmd))

            if process:
                return Popen(cmd, stdout=PIPE, stderr=None, shell=shell)

            result = Command(cmd).run(shell, timeout)
            if result:
                result = (result[0].split('\r\n', 2)[2], result[1]) if 'password:' in result[0] else (result[0].split('\r\n', 1)[1], result[1])

            return result
        except Exception:
            Log.d(traceback.format_exc())

        return None

    def run_app(self, app=None):
        return self.run_on_ios('open {app}'.format(app=app['CodeInfoIdentifier']))

    def dump_keychain(self, dest='/tmp'):
        if self.KEYCHAIN_DUMP:
            Log.d('Dumping Keychain data to {dest} with {bin}'.format(bin=self.KEYCHAIN_DUMP, dest=dest))
            self.run_on_ios('cd {working}; {keychain}'.format(working=dest, keychain=self.KEYCHAIN_DUMP))
        else:
            Log.e('Error: No keychain dump binary found - was prepare_analysis run?')

    def dump_file_protect(self, file):
        if self.DUMP_FILE_PROTECT:
            Log.d('Dumping file protection flags of {file} with {bin}'.format(bin=self.DUMP_FILE_PROTECT, file=file))
            return self.run_on_ios('{dfp} {file}'.format(dfp=self.DUMP_FILE_PROTECT, file=file))[0]
        else:
            Log.e('Error: No file protection dump binary found - was prepare_analysis run?')

    def dump_log(self, app):
        if self.DUMP_LOG:
            Log.d('Dumping logs of {app} with {bin}'.format(bin=self.DUMP_LOG, app=app))
            return self.run_on_ios('{dumplog} {app}'.format(dumplog=self.DUMP_LOG, app=app))[0]
        else:
            Log.e('Error: No dumplog binary found - was prepare_analysis run?')

    def set_proxy(self, ip=None, port=None):
        Log.d("Adding proxy {ip}:{port}".format(ip=ip, port=port))

        prefs = self.get_plist(self.PREF_FILE)

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
            from uuid import uuid4
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
            f.write(dict_to_plist(prefs))
        self.push('/tmp/preferences.plist', '/private/var/preferences/SystemConfiguration')
        self.plist_to_bin(self.PREF_FILE)

        if self.check_dependencies('activator', install=True):
            self.run_on_ios('activator send switch-off.com.a3tweaks.switch.wifi')
            self.run_on_ios('activator send switch-on.com.a3tweaks.switch.wifi')
            return True

        Log.e('Activator not found in the device. Please turn the WiFi off and on again manually')

    def check_dependencies(self, dependency='full', silent=False, install=False):
        Log.d('Checking dependencies: {dep}'.format(dep=dependency))
        passed = True

        if 'full' in dependency or 'connection' in dependency or 'expect' in dependency:
            if not settings.expect:
                passed = False

            if not silent: Log.w('Expect Shell       : {shell}'.format(shell=settings.expect))

        if 'full' in dependency or 'connection' in dependency:
            uname = self.run_on_ios('uname -m')
            if 'Connection refused' in uname[0] or 'Connection closed' in uname[0]:
                if not silent: Log.w('Connection Check : No Connection')
                passed = False

            elif not silent: Log.w('Connection Check : Connected')

        if 'full' in dependency or 'device' in dependency:
            uname = self.run_on_ios('uname -m')[0].lower()

            if 'iphone' not in uname and 'ipad' not in uname and 'ipod' not in uname:
                passed = False

            if not silent: Log.w('Device Check       : {connected}'.format(connected=uname.strip()))

        if 'full' in dependency or 'clutch' in dependency:
            clutch = self.run_on_ios('which Clutch2')[0][:-2]
            if not clutch:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.run_on_ios('apt-get -y install com.iphonecake.clutch2')
                    if not self.check_dependencies('clutch', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('Clutch             : {path}'.format(path=clutch.strip()))

        if 'full' in dependency or 'ipainstaller' in dependency:
            ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]
            if not ipainstaller:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.run_on_ios('apt-get -y install com.slugrail.ipainstaller')
                    if not self.check_dependencies('ipainstaller', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('IPA Installer      : {path}'.format(path=ipainstaller.strip()))

        if 'full' in dependency or 'activator' in dependency:
            activator = self.run_on_ios('which activator')[0][:-2]
            if not activator:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.run_on_ios('apt-get install libactivator')
                    if not self.check_dependencies('activator', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('Activator          : {path}'.format(path=activator.strip()))

        if 'full' in dependency or 'plutil' in dependency:
            if not settings.plutil:
                passed = False

            if not silent: Log.w('Plutil             : {path}'.format(path=settings.plutil.strip()))

        return passed

    def install(self, ipa=None):
        if not ipa:
            return False

        if not self.check_dependencies('ipainstaller', install=True):
            die('Error: No IPA Installer installed on the device')

        if not path.exists(ipa) or not path.isfile(ipa):
            die('Error: Invalid IPA file')

        self.push(ipa, '/tmp')
        settings.ipainstaller = self.run_on_ios('which ipainstaller')[0][:-2]

        name = ipa.rsplit('/', 1)[1] if '/' in ipa else ipa
        result = self.run_on_ios('{ipai} -f -d /tmp/{ipa}'.format(ipai=settings.ipainstaller, ipa=name))[0]
        if 'Failed' in result or 'Invalid' in result:
            die('Error: Failed to install the IPA:{result}'.format(result=result.split('\r\n')[-2:-1][0]))

        if 'successfully' in result.lower():
            self.update_apps_list(False)

            Utils.run('{unzip} -o {ipa} -d /tmp/ipa'.format(unzip=settings.unzip, ipa=ipa))

            from os import listdir
            app = listdir('/tmp/ipa/Payload/').pop()

            self.plist_to_xml('/tmp/ipa/Payload/{app}/Info.plist'.format(app=app), False)
            with open('/tmp/ipa/Payload/{app}/Info.plist'.format(app=app), 'r') as f:
                plist = f.read()

            Utils.run('rm -rf /tmp/ipa/')

            return plist_to_dict(plist)['CFBundleIdentifier']

        return False

    def plist_to_xml(self, file=None, ios=True):
        if not file:
            return None

        if ios:
            self.run_on_ios('plutil -convert xml1 {file}'.format(file=file))
        else:
            Utils.run('plutil -convert xml1 {file}'.format(file=file))

    def plist_to_bin(self, file=None, ios=True):
        if not file:
            return None

        if ios:
            self.run_on_ios('plutil -convert binary1 {file}'.format(file=file))
        else:
            Utils.run('plutil -convert binary1 {file}'.format(file=file))


    def delete(self, file=None):
        if not file:
            return False

        self.run_on_ios('rm -rf {file}'.format(file=file))
        return True

    def push(self, file=None, path=None):
        if not file or not path: return False
        cmd = '{scp} {file} {path}/{end}'.format(scp=settings.scp_to_ios, file=file, path=path, end=file.split('/')[-1])
        results = Utils.run(cmd, True)

        Log.d(results[1])
        return '100%' in results[0]

    def read_file(self, file=None):
        if not file:
            return ''

        return self.run_on_ios('cat {file}'.format(file=file))[0]

    def update_apps_list(self, silent=False):
        if not silent: Log.w('Updating apps list on iOS: may take up to 30 seconds')
        self.run_on_ios('uicache', timeout=30)

    def list_apps(self, silent=False):
        PATHS = [
            '/var/mobile/Library/Caches/com.apple.mobile.installation.plist',
            '/var/mobile/Library/MobileInstallation/LastLaunchServicesMap.plist',
            '/private/var/installd/Library/MobileInstallation/LastLaunchServicesMap.plist'
        ]

        for apps_file in PATHS:
            if self.file_exists(apps_file):
                text = self.read_file(apps_file)

                # check if plain text file
                if '<key>' not in text:
                    self.plist_to_xml(apps_file)
                    text = self.read_file(apps_file)

                apps = plist_to_dict(text)['User']
                if not silent:
                   for app in apps:
                        print('{app} :\n    APP: {bin}\n    DATA: {data}'.format(app=app, bin=apps[app]['Path'], data=apps[app]['Container']))
                return apps

        die('Error: Device OS not supported')

    """
    [Deprecated]
    def list_apps_old(self, silent=False):
        settings.APPS_PATH = settings.APPS_PATH_7 if self.get_ios_version() < 8.0 else (settings.APPS_PATH_8 if self.get_ios_version() < 9.0 else settings.APPS_PATH_9)
        apps = self.run_on_ios('ls -d {appspath}/*/*.app | cut -d"/" -f7-'.format(appspath=settings.APPS_PATH))[0]
        if 'No such file or directory' not in apps:
            settings.iosapps = apps.split('\r\n')[:-1]

            if not silent:
                for i, app in enumerate(settings.iosapps):
                    if app:
                        uuid, name,  = app.split('/')
                        print('{i}) {name}\n    UUID: {uuid}'.format(i=i, name=name, uuid=uuid))
    """

    def get_ios_version(self):
        cmd = 'grep -A 1 "ProductVersion" /System/Library/CoreServices/SystemVersion.plist | tail -n 1 | cut -d">" -f2 | cut -d"<" -f1';
        result = self.run_on_ios(cmd)
        return float(result[0][:3]) if result else None

    def start_tcp_relay(self):
        if not hasattr(settings, 'tcprelay_process'):
            settings.tcprelay_process = Utils.run('{cmd} -t 22:2222'.format(cmd=settings.tcprelay), True, True)
            sleep(1) # tcprelay not working properly without sleep

    def stop_tcp_relay(self):
        if hasattr(settings, 'tcprelay_process'):
            settings.tcprelay_process.kill()

    def file_exists(self, file=None):
        return 'cannot access' not in self.run_on_ios('ls {file}'.format(file=file))[0]

    def get_plist(self, file=None):
        try:
            self.plist_to_xml(file)
            return plist_to_dict(self.read_file(file))
        except Exception:
            Log.e('Error getting the plist {file}'.format(file=file))
            Log.d(traceback.format_exc())
            return {}

    def get_info(self, app=None):
        return self.get_plist('{app}/Info.plist'.format(app=app['Path'].replace(' ', '\ ')))

    def get_entitlements(self, binary=None):
        text = self.run_on_ios('ldid -e {app}'.format(app=binary))[0]
        if text.count('</plist>') > 1:
            stext = text.split('\r\n')
            text = '\r\n'.join([i for i in stext[:len(stext)/2]])
        return plist_to_dict(text)

    def pull(self, file=None, path=None):
        if not file or not path: return False
        cmd = '{scp} {file} {path}'.format(scp=settings.scp_from_ios, file=file, path=path)
        results = Utils.run(cmd, True)
        return '100%' in results[0]

    def get_archs(self, binary=None):
        result = []
        if binary:
            out = self.run_on_ios('otool -hv {binary}'.format(binary=binary))[0]
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
                        Log.e('Other Arch found. Please check manually')

        return result

def dict_to_plist(text):
    import plistlib
    return plistlib.writePlistToString(text)

def plist_to_dict(text=None):
    if not text:
        return {}

    import plistlib
    return plistlib.readPlistFromString(text)