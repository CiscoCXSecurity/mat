# python modules
from subprocess import Popen, PIPE
from os import path, remove
import traceback

# launching stuff problems
from time import sleep

# local imports
from utils import Utils, Log
import settings

################################################################################
#    ANDROID UTILS FUNCTIONS
################################################################################

class AndroidUtils(object):

    INSTALL_PATH = '/system/xbin'

    def __init__(self):
        self.ADB           = ADB(adb=settings.adb)
        self.CHECKS_PASSED = {}
        self.launched      = {}
        self.CREATED_AVD   = False

        self.ADB.start_server()

        devices = self.devices()
        if len(devices) == 0:
            Log.d('Error: No devices connected.')
        settings.device = settings.device or (devices[0] if devices else None)
        self.ADB.set_device(settings.device)

    ############################################################################
    #    ADB WRAPPER FUNCTIONS
    ############################################################################

    def launch_app(self, package, device=None):
        if device not in self.launched or not self.launched[device]:
            self.launched[device] = True
            self.ADB.start_app_on(device, package) # launch the app
            sleep(5)

    def query_provider(self, provider, projection='', selection=''):
        if '"' in projection or '"' in selection:
            Log.d('Error: cannnot query providers with "')
            return ('', '')

        projection = '--projection \\\"{projection}\\\"'.format(projection=projection) if projection else ''
        selection = '--where \\\"{selection}\\\"'.format(selection=selection) if selection else ''
        query = 'shell su -c "content query --uri \'content://{provider}\' {projection} {selection}"'.format(provider=provider, projection=projection, selection=selection)
        return self.ADB._run_on_device(query, shell=True)

    def read_provider(self, provider, provider_path=''):
        query = 'shell su -c "content read --uri \'content://{provider}{path}\'"'.format(provider=provider, path=provider_path)
        return self.ADB._run_on_device(query, shell=True)

    def find_world_files(self, starting_path, permissions='r'):
        find_command = 'shell su -c find ' + starting_path + ' "\( -type b -o -type c -o -type f -o -type s \) -perm -o=' + permissions + ' \-exec ls {} \;"'
        return self.ADB._run_on_device(find_command)[0]

    def data_path(self, package):
        return '{data}/{package}/'.format(data=self.ADB.DATA_FOLDER, package=package)

    def app_path(self, package):
        return self.ADB.app_path(package)

    def pull(self, file, dest):
        self.ADB.pull(file, dest)

    def push(self, file, dest):
        self.ADB.push(file, dest)

    def get_apk(self, package):
        return self.ADB.apk(package).strip()

    def processes(self, device=None, root=True):
        device = device or settings.device
        return self.ADB.processes(device, root)

    def has(self, package, device):
        return package in self.ADB.packages_on(device)

    def list_apps(self, silent=False):
        packages = self.ADB.packages()
        if silent: return packages
        for package in packages:
            print package

    def devices(self):
        return self.ADB.devices()

    def install_on(self, device, apk):
        return self.ADB.install_on(device, apk)

    def install(self, apk=None):
        return self.ADB.install(apk)

    def unlocked(self, device):
        return self.ADB.unlocked(device)

    def online(self, device):
        return self.ADB.online(device)

    def pull_data_content(self, package, dest):
        return self.ADB.pull_data_content(package, dest)

    def set_device(self, device):
        return self.ADB.set_device(device)

    def device(self):
        return self.ADB.device()

    def avds(self):
        #return [avd.split(":", 1)[-1].strip() for avd in Utils.run('{avdmanager} list avd | {grep} Name'.format(avdmanager=settings.avdmanager, grep=settings.grep))[0].split('\n')]
        return Utils.run('{avdmanager} list avd'.format(avdmanager=settings.avdmanager))[0]

    def run_on_device(self, command, su=False):
        su = 'su -c' if su else ''
        return self.ADB._run_on_device('shell {su} {command}'.format(su=su, command=command))

    ############################################################################
    #    UTILS FUNCTIONS
    ############################################################################

    def get_string(self, name, resources_folder):
        strings_file = '{res}/values/strings.xml'.format(res=resources_folder)
        if not path.exists(strings_file):
            return None

        name = name.replace('@string/', '')
        item = Utils.grep(name, strings_file)

        return item.popitem()[1][0]['code'].split(name, 1)[-1].split('>', 1)[-1].split('<', 1)[0] if len(item) > 0 else None

    def providers(self, manifest, working_folder):
        import re
        regex = r'content://[a-zA-Z0-1.-@/]+'
        providers = []
        strings = Utils.grep(regex, working_folder)
        for f in strings:
            for finding in strings[f]:
                providers += [re.search(regex, finding['code']).group().split('://', 1)[-1]]

        manifest_providers = manifest.providers()
        for provider in manifest_providers:
            provider['name'] = self.get_string(provider['name'], '{working}/decompiled-app/res'.format(working=working_folder)) if '@string' in provider['name'] else provider['name']
            provider['authority'] = self.get_string(provider['authority'], '{working}/decompiled-app/res'.format(working=working_folder)) if '@string' in provider['authority'] else provider['authority']
            providers += ['{auth}{name}'.format(auth=provider['authority'], name=provider['name']) if provider['name'].startswith('.') else provider['authority']]

        new_providers = []
        for provider in providers:
            new_providers += [provider[:-1] if provider.endswith('/') else '{provider}/'.format(provider=provider)]

        return sorted(set(providers + new_providers))

    def create_avd(self, name='MAT-Testing', api='26'):
        Log.w('Creating AVD {name} with android api {api}'.format(name=name, api=api))

        Log.d('Accepting Licenses')
        Utils.run('yes | {sdkmanager} --licenses'.format(sdkmanager=settings.sdkmanager), shell=True)

        Log.d('Updating sdkmanager')
        Utils.run('echo y | {sdkmanager} --update'.format(sdkmanager=settings.sdkmanager), shell=True)

        Log.d('Installing api with sdkmanager')
        if not any(s in Utils.run('{sdkmanager} "system-images;android-{api};google_apis;x86"'.format(sdkmanager=settings.sdkmanager, api=api), shell=True)[0] for s in ['done', '100%']):
            Log.d('Could not install android api {api}. Install it manually.'.format(api=api))
            return False

        Log.d('Creating AVD {name}'.format(name=name))
        if 'Error' in Utils.run('{avdmanager} create avd -n {name} -k "system-images;android-{api};google_apis;x86" -d "Nexus 6P"'.format(avdmanager=settings.avdmanager, name=name, api=api), shell=True)[0]:
            Log.d('Could not create AVD {name}'.format(name=name))
            return False

        avdlist = self.avds()
        avdpath = False
        for line in avdlist.split('\n'):
            if avdpath and 'Path' in line:
                avdpath = line.split(':')[1].strip()
                break
            if name in line:
                avdpath = True

        if not avdpath or not path.exists('{avdpath}/config.ini'.format(avdpath=avdpath)):
            Log.d('Could not find the path for AVD {name}'.format(name=name))
            return False

        Log.d('Adding hardware GPU settings')
        GPU_HARDWARE='hw.gpu.enabled=yes\nhw.gpu.mode=host\nsdcard.size=128M\nshowDeviceFrame=no\nskin.dynamic=yes\nskin.name=1080x1920\nskin.path=_no_skin\nskin.path.backup=_no_skin'
        with open('{avdpath}/config.ini'.format(avdpath=avdpath), 'a') as f:
            f.write(GPU_HARDWARE)

        settings.avd = name
        self.CREATED_AVD = True
        return True

    def get_smali_method(self, method=None, file=None):
        if not method or not file or not path.exists(file):
            return None

        with open(file, 'r') as f:
            smali = f.read()

        smali_method = ''
        for line in smali.split('\n'):
            if '.method' in line and method in line and not smali_method:
                smali_method = line
                continue

            if smali_method:
                smali_method += line + '\n'

            if smali_method and '.end method' in line:
                return smali_method

        return smali_method

    def clean(self):
        self.ADB.clean()
        self.ADB.stop_server()

    def install_busy_box(self, dest="/system/xbin"):
        Log.w('Installing Busy Box On: {path}'.format(path=dest))

        if 'aarch64' not in self.ADB._run_on_device('shell uname -a')[0]:
            Log.d('Error: Can\'t install busybox (not x64 arch), please do it manually')
            return False

        Log.d('Pushing busybox to: {device}'.format(device=self.ADB.DEVICE))
        self.push('{busybox}'.format(busybox=settings.busybox), '{tmp}/'.format(tmp=self.ADB.TMP_FOLDER))

        Log.d('Remounting /system as rw')
        self.ADB._run_on_device('shell su -c mount -o remount,rw /system')

        Log.d('Moving binaries to /system/xbin')
        self.ADB._run_on_device('shell su -c cp "{tmp}/busybox" {dest}/'.format(tmp=self.ADB.TMP_FOLDER, dest=dest))
        self.ADB._run_on_device('shell su -c chown root:shell {dest}/*'.format(dest=dest))
        self.ADB._run_on_device('shell su -c chmod 755 {dest}/*'.format(dest=dest))

        Log.d('Remounting /system as ro')
        self.ADB._run_on_device('shell su -c mount -o remount,ro /system')

        Log.d('Removing temp files')
        self.ADB._run_on_device('shell su -c rm -rf {tmp}/busybox'.format(tmp=self.ADB.TMP_FOLDER))

        return True

    def compile(self, app_path):
        Log.d('Compiling Android Application: {path}'.format(path=app_path))

        yml = YML(app_path, settings.apkfilename)
        settings.apkfilename = '{name}-new.apk'.format(name=yml.apk_file_name.replace('.apk', ''))

        Log.w('Compiling Android Application in {path} to {name}'.format(path=app_path, name=settings.apkfilename))
        Utils.run('{apktool} b -o {name} {path}'.format(apktool=settings.apktool, name=settings.apkfilename, path=app_path))

        if path.exists(settings.apkfilename):
            signed = '{name}-signed.apk'.format(name=settings.apkfilename.replace('-new.apk', ''))

            Log.w('Signing Android Application in {name} to {signed}'.format(name=settings.apkfilename, signed=signed))
            Utils.run('{java} -jar {signapk} {cert} {pk8} {name} {signed}'.format(java=settings.java, signapk=settings.signjar, cert=settings.cert, pk8=settings.pk8, name=settings.apkfilename, signed=signed))

            if not path.exists(signed):
                Log.d('Signing Android Application Failed')

            Log.w('Deleting Unsigned Android Application {name}'.format(name=settings.apkfilename))
            remove(settings.apkfilename)

        else:
            Log.d('Compiling Android Application Failed')

    def check_dependencies(self, dependencies=['full'], silent=True, install=False, force=False):
        """
        top_level_dependencies     = ['full', 'static', 'dynamic', 'signing', 'avd']
        binaries_path_dependencies = ['adb', 'sdkmanager', 'avdmanager', 'emulator', 'apktool', 'jdcli', 'dex2jar', 'signjar', 'cert', 'pk8']
        """

        Log.d('Checking dependencies: {dep}'.format(dep=dependencies))

        ########################################################################
        # CHECK PRE REQUESITES
        ########################################################################
        if not isinstance(dependencies, list):
            Log.d('Error: Dependencies must be a list')
            return False

        valid_dependencies   = ['full', 'static', 'dynamic', 'signing', 'avd']
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
        # STATIC DEPENDENCIES
        ########################################################################
        if 'full' in dependencies or 'static' in dependencies:
            self.CHECKS_PASSED['static'] = True

            static_dependencies = ['apktool', 'jdcli', 'dex2jar']
            for d in static_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['dynamic'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

        ########################################################################
        # DYNAMIC DEPENDENCIES
        ########################################################################
        if 'full' in dependencies or 'dynamic' in dependencies:
            self.CHECKS_PASSED['dynamic'] = True

            dynamic_dependencies = ['adb']
            for d in dynamic_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['dynamic'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

            if not self.device():
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['dynamic'] = False
            if not silent: Log.w('using device: {device}'.format(device=self.device()))

        ########################################################################
        # AVD DEPENDENCIES
        ########################################################################
        if 'full' in dependencies or 'avd' in dependencies:
            self.CHECKS_PASSED['avd'] = True

            avd_dependencies = ['avdmanager', 'sdkmanager', 'emulator']
            for d in avd_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['avd'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

            if self.CHECKS_PASSED['avd'] and install and settings.avd not in self.avds():
                self.create_avd()
            if self.CHECKS_PASSED['avd'] and settings.avd not in self.avds():
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['avd'] = False
            if not silent: Log.w('AVD {name} Found: {found}'.format(name=settings.avd, found=self.CHECKS_PASSED['avd']))

        ########################################################################
        # SIGNING DEPENDENCIES
        ########################################################################
        if 'full' in dependencies or 'signing' in dependencies:
            self.CHECKS_PASSED['signing'] = True

            signing_dependencies = ['signjar', 'cert', 'pk8']
            for d in signing_dependencies:
                if not path.exists(getattr(settings, d)):
                    self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['signing'] = False
                if not silent: Log.w('{bin} path: {path}'.format(bin=d, path=getattr(settings, d)))

        return all([self.CHECKS_PASSED[d] for d in self.CHECKS_PASSED if d in dependencies])


class ADB(object):

    TMP_FOLDER  = '/sdcard/mat-tmp'
    DATA_FOLDER = '/data/data'
    APP_FOLDER  = '/data/app'

    def __init__(self, device=None, adb=None):
        self.DEVICE = device
        self.BIN    = adb
        if self.DEVICE:
            self.make_temp_folder()

    def _run(self, command, shell=False):
        return Utils.run('{adb} {command}'.format(adb=self.BIN, command=command), shell=shell)

    def _run_on_device(self, command, device=None, shell=False):
        device = device or self.DEVICE
        if not device:
            Log.d('Error: No devices connected. Could not run: {command}'.format(command=command))
            return []
        return self._run('-s {device} {command}'.format(device=device, command=command), shell=shell)

    def device(self):
        return self.DEVICE

    def set_device(self, device):
        self.DEVICE = device
        self.make_temp_folder()

    def start_server(self):
        self._run('start-server')

    def stop_server(self):
        self._run('stop-server')

    def make_dir(self, path):
        self._run_on_device('shell su -c mkdir {path}'.format(path=path))

    def make_temp_folder(self):
        return self.make_dir(self.TMP_FOLDER)

    def list(self, path):
        return self._run_on_device('shell ls {path}'.format(path=path))[0].split('\n')

    def devices(self):
        return [line.split('\t')[0] for line in filter(lambda line: line != '', self._run('devices')[0].split('\n')[1:])]

    def online(self, device):
        for d in self._run('devices')[0].split('\n'):
            if device in d and 'device' in d:
                return True
        return False

    def packages_on(self, device):
        return [line.split('=')[1].strip() if '=' in line else line for line in self._run_on_device('shell pm list packages -f', device=device)[0].split('\n')[:-1]]

    def packages(self):
        return self.packages_on(self.DEVICE)

    def install_on(self, device, apk):
        return self._run_on_device('install {apk}'.format(apk=apk), device=device)

    def install(self, apk=None):
        return self.install_on(self.DEVICE, apk)

    def uninstall_from(self, device, package):
        return self._run_on_device('uninstall {package}'.format(package=package), device=device)

    def uninstall(self, package=None):
        return self.uninstall_from(self.DEVICE, package)

    def start_activity_on(self, device, activity):
        return self._run_on_device('shell am start -n {activity}'.format(activity=activity), device=device)

    def start_activity(self, activity):
        return self.start_activity_on(self.DEVICE, activity)

    def forward(self, local, remote):
        return self._run_on_device('forward {local} {remote}'.format(local=local, remote=remote))

    def removeForward(self, local):
        return self._run_on_device('forward --remove {local}'.format(local=local))

    def start_app_on(self, device, package):
        if device == None:
            device = self.DEVICE
        return self._run_on_device('shell monkey -p {package} -c android.intent.category.LAUNCHER 1'.format(package=package), device=device)[0]

    def start_app(self, package=None):
        return self.start_app_on(self.DEVICE, package)

    def logcat(self, device, count):
        return self._run_on_device('logcat -t 50'.format(device=device))[0]

    def unlocked(self, device):
        result = self._run_on_device('shell dumpsys power | grep mHoldingDisplaySuspendBlocker', device=device, shell=True)[0]
        while 'mHolding' not in result:
            sleep(3)
            result = self._run_on_device('shell dumpsys power | grep mHoldingDisplaySuspendBlocker', device=device, shell=True)[0]
        return all('true' in option.split('=', 1)[1] for option in result.split('\n')[:-1])

    def pull_data_content(self, package, dest):
        self._run_on_device('shell su -c cp -r {data}/{package} {tmp}/{package}'.format(package=package, data=ADB.DATA_FOLDER, tmp=ADB.TMP_FOLDER))
        self._run_on_device('pull {tmp}/{package} {data}'.format(package=package, data=dest, tmp=ADB.TMP_FOLDER))

    def pull(self, file, dest):
        self._run_on_device('shell su -c cp {file} {tmp}/'.format(tmp=ADB.TMP_FOLDER, file=file))
        return self._run_on_device('pull {tmp}/{file} {dest}'.format(tmp=ADB.TMP_FOLDER, dest=dest, file=file.rsplit('/', 1)[1]))

    def push(self, file, dest):
        return self._run_on_device('push {file} {dest}'.format(dest=dest, file=file))

    def apk(self, package):
        package = self._run_on_device('shell pm path {package}'.format(package=package))[0]
        return package.split(':', 1)[1] if package else package

    def app_path(self, package):
        package = self._run_on_device('shell pm path {package}'.format(package=package))[0]
        return package.split(':', 1)[1].rsplit('/', 1)[0] if package else package


    def exists(self, file):
        return 'No such file' not in self._run_on_device('shell su -c ls {file}'.format(file=file))[0]

    def processes(self, device, root=True):
        return self._run_on_device('shell su -c ps', device=device)[0] if root else self._run_on_device('shell ps', device=device)[0]

    def clean(self):
        self._run_on_device('shell su -c rm -rf {tmp}'.format(tmp=ADB.TMP_FOLDER))


class Manifest(object):

    def __init__(self, fpath='.', apk_file_name='unknown.apk'):
        import xml.etree.ElementTree as ET

        # create xml parser
        with open('{path}/AndroidManifest.xml'.format(path=fpath), 'r') as f:
            self.root = ET.fromstring(f.read().replace('xmlns:android="http://schemas.android.com/apk/res/android" ','').replace('android:',''))

        self.yml     = YML(fpath, apk_file_name)
        self.package = self.root.get('package')
        self.version = self.yml.version or self.root.get('platformBuildVersionName', '')

    def permissions(self):
        return [p.get('name', '') for p in self.root.findall('uses-permission')]

    def providers(self):
        providers = []
        for provider in self.root.find('application').findall('provider'):
            providers += [{
                'authority': provider.get('authorities', ''),
                'exported': provider.get('exported', 'false') == 'true',
                'name': provider.get('name', '')
            }]
        return providers

    def secret_codes(self):
        codes = []
        for r in self.root.find('application').findall('receiver'):
            for f in r.findall('intent-filter'):
                for d in f.findall('data'):
                    scheme = d.get('scheme', '')
                    host = d.get('host', '')
                    if scheme and host and 'android_secret_code' in scheme:
                        codes += [host]
        return codes

    def browsable(self):
        browsable_uris    = []
        browsable_classes = []
        for activity in self.root.find('application').findall('activity'):
            for intentfilter in activity.findall('intent-filter'):
                for category in intentfilter.findall('category'):
                    if category.get('name') == "android.intent.category.BROWSABLE":
                        browsable_classes += [activity.get('name', '')]
                        for data in intentfilter.findall('data'):
                            scheme, host= data.get('scheme', ''), data.get('host', '')
                            port = ':{port}'.format(port=data.get('port', '')) if data.get('port', '') else ''
                            uri_path, prefix, pattern = data.get('path', ''), data.get('pathPrefix', ''), data.get('pathPattern', '')
                            browsable_uris += ['{scheme}://{host}{port}{path}{prefix}{pattern}'.format(scheme=scheme, host=host, port=port, path=uri_path, prefix=prefix, pattern=pattern)]
                        break

        return (sorted(set(browsable_classes)), sorted(set(browsable_uris)))

    def main_activity(self, package):
        for a in self.root.find('application').findall('activity'):
            intentf = a.find('intent-filter')
            action = intentf.find('action') if intentf is not None else None
            if action is not None and action.get('name', '') == 'android.intent.action.MAIN':
                return a.get('name', '').replace(package, '')

    def allows_backup(self):
        return self.root.find('application').get('allowBackup', 'false') == 'true'

    def debuggable(self):
        return self.root.find('application').get('debuggable', 'false') == 'true'

    def get_sdk(self, sdk='min'):
        result = self.root.find('application').find('uses-sdk').get('{sdk}SdkVersion'.format(sdk=sdk.capitalize()), '') if self.root.find('application').find('uses-sdk') else self.yml.get_sdk(sdk)
        return result if result else self.yml.get_sdk(sdk)

class YML(object):

    YML_FILE = 'apktool.yml'

    def __init__(self, fpath='.', apk_file_name="unkown.apk"):
        self.raw = ''
        if path.exists('{path}/{yml}'.format(path=fpath, yml=YML.YML_FILE)):
            with open('{path}/{yml}'.format(path=fpath, yml=YML.YML_FILE), 'r') as f:
                self.raw = f.read()

        self.min_sdk      = self.raw.split('minSdkVersion:')[1].split('\'')[1].strip() if 'minSdkVersion' in self.raw else '-1'
        self.max_sdk      = self.raw.split('maxSdkVersion:')[1].split('\'')[1].strip() if 'maxSdkVersion' in self.raw else '-1'
        self.target_sdk   = self.raw.split('targetSdkVersion:')[1].split('\'')[1].strip() if 'targetSdkVersion' in self.raw else '-1'
        self.apk_filename = self.raw.split('apkFileName:')[1].split('\n')[0].strip() if 'apkFileName' in self.raw else apk_file_name
        self.version      = self.raw.split('versionName:')[1].split('\n')[0].strip() if 'versionName' in self.raw else ''

    def get_sdk(self, sdk='min'):
        return getattr(self, '{sdk}_sdk'.format(sdk=sdk.lower()))

