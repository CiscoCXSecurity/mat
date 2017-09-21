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
        self.DROZER        = None
        self.CHECKS_PASSED = {}
        self.launched      = {}
        self.CREATED_AVD   = False

        self.ADB.start_server()

        devices = self.devices()
        if len(devices) == 0:
            Log.e('Error: No devices connected.')
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

    ############################################################################
    #    DROZER FUNCTIONS
    ############################################################################

    def get_drozer(self):
        if self.DROZER:
            return self.DROZER

        self.DROZER = Drozer(self.ADB)
        return self.DROZER

    ############################################################################
    #    UTILS FUNCTIONS
    ############################################################################

    def create_avd(self, name='MAT-Testing', api='26'):
        Log.w('Creating AVD {name} with android api {api}'.format(name=name, api=api))

        Log.d('Installing api with sdkmanager')
        if 'done' not in Utils.run('{sdkmanager} "system-images;android-{api};google_apis;x86"'.format(sdkmanager=settings.sdkmanager, api=api), shell=True)[0]:
            Log.e('Could not install android api {api}. Install it manually.'.format(api=api))
            return False

        Log.d('Creating AVD {name}'.format(name=name))
        if 'Error' in Utils.run('{avdmanager} create avd -n {name} -k "system-images;android-{api};google_apis;x86" -d "Nexus 6P"'.format(avdmanager=settings.avdmanager, name=name, api=api), shell=True)[0]:
            Log.e('Could not create AVD {name}'.format(name=name))
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
            Log.e('Could not find the path for AVD {name}'.format(name=name))
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
        if self.DROZER:
            self.DROZER.stop()
        self.ADB.clean()
        self.ADB.stop_server()

    def install_busy_box(self, dest="/system/xbin"):
        Log.w('Installing Busy Box On: {path}'.format(path=dest))

        #http://android.stackexchange.com/questions/123183/how-do-i-install-dropbear-ssh-on-android
        if 'aarch64' not in self.ADB._run_on_device('shell uname -a')[0]:
            Log.e('Error: Can\'t install busybox (not x64 arch), please do it manually')
            return False

        TMP_FOLDER = '/tmp/bb-bins'

        Log.d('Pushing binaries to: {device}'.format(device=self.ADB.DEVICE))
        Utils.run('{unzip} -o {bins} -d {tmp}'.format(unzip=settings.unzip, bins=settings.busybox_bins, tmp=TMP_FOLDER))

        self.ADB.make_dir('{tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))
        self.push('{tmp}/*'.format(tmp=TMP_FOLDER), '{tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))

        Log.d('Remounting /system as rw')
        self.ADB._run_on_device('shell su -c mount -o remount,rw /system')

        Log.d('Moving binaries to /system/xbin')
        self.ADB._run_on_device('shell su -c cp "{tmp}/bbins/*" {dest}/'.format(tmp=self.ADB.TMP_FOLDER, dest=dest))
        self.ADB._run_on_device('shell su -c chown root:shell {dest}/*'.format(dest=dest))
        self.ADB._run_on_device('shell su -c chmod 755 {dest}/*'.format(dest=dest))

        Log.d('Installing busybox and creating symlinks')
        self.ADB._run_on_device('shell su -c {dest}/busybox --install {dest}'.format(dest=dest))
        self.ADB._run_on_device('shell su -c ln -s {dest}/dropbearmulti {dest}/dropbear'.format(dest=dest))
        self.ADB._run_on_device('shell su -c ln -s {dest}/dropbearmulti {dest}/dbclient'.format(dest=dest))
        self.ADB._run_on_device('shell su -c ln -s {dest}/dropbearmulti {dest}/ssh'.format(dest=dest))
        self.ADB._run_on_device('shell su -c ln -s {dest}/dropbearmulti {dest}/dropbearkey'.format(dest=dest))
        self.ADB._run_on_device('shell su -c ln -s {dest}/dropbearmulti {dest}/dropbearconvert'.format(dest=dest))

        Log.d('Remounting /system as ro')
        self.ADB._run_on_device('shell su -c mount -o remount,ro /system')

        Log.d('Removing garbage files')
        Utils.run('rm -rf {tmp}'.format(tmp=TMP_FOLDER))
        self.ADB._run_on_device('shell su -c rm -rf {tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))

        return True

    def setup_ssh(self, key=None, autostart=False):
        """
        Deprecated - Used to setup proxy on android - not working on newwer versions
        """
        Log.w('Setting up Dropbear on: {device}'.format(device=self.ADB.DEVICE))

        DROPBEAR_DATA = '/data/dropbear'
        DROPBEAR_SSH  = '{data}/.ssh'.format(data=DROPBEAR_DATA)
        RSA_KEY       = 'dropbear_rsa_host_key'
        DSS_KEY       = 'dropbear_dss_host_key'

        Log.d('Creating Dropbear Folders')

        if not self.ADB.exists(DROPBEAR_DATA):
            self.ADB.make_dir(DROPBEAR_DATA)
        self.ADB._run_on_device('shell su -c chmod 755 {data}'.format(data=DROPBEAR_DATA))

        if key and path.exists(key):
            Log.d('Setting up authorized keys with: {key}'.format(key=key))
            if not self.ADB.exists(DROPBEAR_SSH):
                self.ADB.make_dir(DROPBEAR_SSH)
            self.ADB._run_on_device('shell su -c chmod 700 {data}'.format(data=DROPBEAR_SSH))
            self.ADB.push(key, '{tmp}/authorized_keys'.format(tmp=self.ADB.TMP_FOLDER))
            self.ADB._run_on_device('shell su -c mv {tmp}/authorized_keys {ssh}/authorized_keys'.format(tmp=self.ADB.TMP_FOLDER, ssh=DROPBEAR_SSH))
            self.ADB._run_on_device('shell su -c chown root: {ssh}/authorized_keys'.format(ssh=DROPBEAR_SSH))
            self.ADB._run_on_device('shell su -c chmod 600 {ssh}/authorized_keys'.format(ssh=DROPBEAR_SSH))

        if autostart and not self.ADB.exists('/etc/init.local.rc') or 'dropbear' not in self.ADB._run_on_device('shell cat /etc/init.local.rc')[0]:
            CONTENT = '\n# start Dropbear (ssh server) service on boot\nservice sshd /system/xbin/dropbear -s\n   user  root\n   group root\n   oneshot\n'
            FILE = ''
            if self.ADB.exists('/etc/init.local.rc'):
                FILE = self.ADB._run_on_device('shell su -c cat /etc/init.local.rc')[0]

            Log.d('Updating Autostart Script')
            FILE = '{file}\n{content}'.format(file=FILE, content=CONTENT)
            with open('/tmp/init.local.rc', 'w') as f:
                f.write(FILE)

            self.ADB.push('/tmp/init.local.rc', '{tmp}/init.local.rc'.format(tmp=self.ADB.TMP_FOLDER))

            Log.d('Remounting /system as rw')
            self.ADB._run_on_device('shell su -c mount -o remount,rw /system')
            self.ADB._run_on_device('shell su -c mv {tmp}/init.local.rc /etc/init.local.rc'.format(tmp=self.ADB.TMP_FOLDER))

            Log.d('Remounting /system as ro')
            self.ADB._run_on_device('shell su -c mount -o remount,ro /system')

    def compile(self, appPath):
        Log.d('Compiling Android Application: {path}'.format(path=appPath))

        yml = YML(appPath)
        settings.apkfilename = '{name}-new.apk'.format(name=yml.apkFileName.replace('.apk', ''))

        Log.w('Compiling Android Application in {path} to {name}'.format(path=appPath, name=settings.apkfilename))
        Utils.run('{apktool} b -o {name} {path}'.format(apktool=settings.apktool, name=settings.apkfilename, path=appPath))

        if path.exists(settings.apkfilename):
            signed = '{name}-signed.apk'.format(name=settings.apkfilename.replace('-new.apk', ''))

            Log.w('Signing Android Application in {name} to {signed}'.format(name=settings.apkfilename, signed=signed))
            Utils.run('{java} -jar {signapk} {cert} {pk8} {name} {signed}'.format(java=settings.java, signapk=settings.signjar, cert=settings.cert, pk8=settings.pk8, name=settings.apkfilename, signed=signed))

            if not path.exists(signed):
                Log.e('Signing Android Application Failed')

            Log.w('Deleting Unsigned Android Application {name}'.format(name=settings.apkfilename))
            remove(settings.apkfilename)

        else:
            Log.e('Compiling Android Application Failed')

    def check_dependencies(self, dependencies=['full'], silent=True, install=False, force=False):
        """
        top_level_dependencies     = ['full', 'static', 'dynamic', 'signing', 'drozer', 'avd']
        binaries_path_dependencies = ['adb', 'sdkmanager', 'avdmanager', 'emulator', 'apktool', 'jdcli', 'dex2jar', 'signjar', 'cert', 'pk8']
        """

        Log.d('Checking dependencies: {dep}'.format(dep=dependencies))

        ########################################################################
        # CHECK PRE REQUESITES
        ########################################################################
        if not isinstance(dependencies, list):
            Log.e('Error: Dependencies must be a list')
            return False

        valid_dependencies   = ['full', 'static', 'dynamic', 'signing', 'drozer', 'avd']
        invalid_dependencies = list(set(dependencies)-set(valid_dependencies))
        if invalid_dependencies:
            Log.e('Error: The following dependencies cannot be checked: {deps}'.format(deps=', '.join(invalid_dependencies)))
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
        # DROZER DEPENDENCIES
        ########################################################################
        if 'full' in dependencies or 'drozer' in dependencies:
            self.CHECKS_PASSED['drozer'] = True

            if not path.exists(settings.drozer):
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['drozer'] = False
            if not silent: Log.w('drozer path: {path}'.format(path=settings.drozer))

            if install and self.device() and not self.has(Drozer.PACKAGE, self.device()):
                self.install(settings.drozer_agent)
            if not self.device() or not self.has(Drozer.PACKAGE, self.device()):
                self.CHECKS_PASSED['full'] = self.CHECKS_PASSED['drozer'] = False
            if not silent: Log.w('drozer agent APK installed: {path}'.format(path=self.CHECKS_PASSED['drozer']))

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
            Log.e('Error: No device connected. Could not run: {command}'.format(command=command))
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

    def exists(self, file):
        return 'No such file' not in self._run_on_device('shell su -c ls {file}'.format(file=file))[0]

    def processes(self, device, root=True):
        return self._run_on_device('shell su -c ps', device=device)[0] if root else self._run_on_device('shell ps', device=device)[0]

    def clean(self):
        self._run_on_device('shell su -c rm -rf {tmp}'.format(tmp=ADB.TMP_FOLDER))

class Drozer(object):

    PACKAGE       = 'com.mwr.dz'
    MAIN_ACTIVITY = '.activities.MainActivity'
    LOCAL         = 'tcp:31415'
    REMOTE        = 'tcp:31415'

    def __init__(self, adb):
        self.ADB    = adb
        self.DROZER = settings.drozer
        self.start()

    def start(self):
        self.ADB.start_activity('{package}/{activity}'.format(package=Drozer.PACKAGE, activity=Drozer.MAIN_ACTIVITY))
        self.ADB.forward(Drozer.LOCAL, Drozer.REMOTE)

    def installed(self,):
        return Drozer.PACKAGE in self.ADB.packages()

    def main_activity(self, package):
        return Drozer.info().split('\n')[1].strip().replace(package, '')

    def _run(self, command, shell=False):
        output = Utils.run('{drozer} console connect -c {command}'.format(drozer=self.DROZER, command=command), shell)
        if output[1]:
            Log.e('Error: Drozer error: {error}'.format(error=output[1]))
            return ['','']
        return output

    def info(self, package):
        return self._run('"run app.package.info -a {package}"'.format(package=package), True)[0]

    def surface(self, package):
        return self._run('"run app.package.attacksurface {package}"'.format(package=package), True)[0]

    def activities(self, package):
        return self._run('"run app.activity.info -a {package}"'.format(package=package), True)[0]

    def services(self, package):
        return self._run('"run app.service.info -a {package}"'.format(package=package), True)[0]

    def providers(self, package):
        return self._run('"run app.provider.info -a {package}"'.format(package=package), True)[0]

    def receivers(self, package):
        return self._run('"run app.broadcast.info -a {package}"'.format(package=package), True)[0]

    def traversal(self, package):
        return self._run('"run scanner.provider.traversal -a {package}"'.format(package=package), True)[0]

    def injection(self, package):
        return self._run('"run scanner.provider.injection -a {package}"'.format(package=package), True)[0]

    def uris(self, package):
        return self._run('"run scanner.provider.finduris -a {package}"'.format(package=package), True)[0]

    def tables(self, package):
        return self._run('"run scanner.provider.sqltables -a {package}"'.format(package=package), True)[0]

    def native(self, package):
        return self._run('"run scanner.misc.native -a {package}"'.format(package=package), True)[0]

    def codes(self):
        return self._run('"run scanner.misc.secretcodes"', True)[0]

    def writable(self, package):
        return self._run('"run scanner.misc.writablefiles -p /data/data/{package}"'.format(package=package), True)[0]

    def suid(self, package):
        return self._run('"run scanner.misc.sflagbinaries -p -t /data/data/{package}"'.format(package=package), True)[0]

    def readable(self, package):
        return self._run('"run scanner.misc.readablefiles -p /data/data/{package}"'.format(package=package), True)[0]

    def browsable(self, package):
        return self._run('"run scanner.activity.browsable -a {package}"'.format(package=package), True)[0]

    def stop(self):
        self.ADB.removeForward(Drozer.LOCAL)

    @staticmethod
    def parse_output(key=None, output=None):
        if key == '' and output:
            return [line for line in filter(lambda line: line != '', output.split('\n')[1:-1])]

        if not key or not output:
            return ''

        result = []
        save = False
        for line in output.split('\n'):
            if save:
                if line.strip() == '':
                    break
                result.append(line.strip())
            if key in line:
                save = True

        return result


class Manifest(object):

    NAMESPACE = 'android'
    URI       = 'http://schemas.android.com/apk/res/android'

    def __init__(self, fpath='.'):
        import xml.etree.ElementTree as ET

        # create xml parser
        self.xml     = ET.parse('{path}/AndroidManifest.xml'.format(path=fpath))
        self.root    = self.xml.getroot()
        self.yml     = YML(fpath)
        self.package = self.root.get('package')
        self.version = self.yml.version or self.root.get('platformBuildVersionName')

        # this is used to write the manifest correctly
        ET.register_namespace(Manifest.NAMESPACE, Manifest.URI)

    def permissions(self):
        return [p.get('{' + Manifest.URI + '}name') for p in self.root.findall('uses-permission')]

    def main_activity(self):
        for a in self.root.find('application').findall('activity'):
            intentf = a.find('intent-filter')
            action = intentf.find('action') if intentf else None
            # needs to have != None for some reason
            if action != None and action.get('{' + Manifest.URI + '}name') == 'android.intent.action.MAIN':
                return a.get('{' + Manifest.URI + '}name').replace(settings.package, '')

    def allows_backup(self):
        return self.root.find('application').get('{' + Manifest.URI + '}allowBackup') == 'true'

    def debuggable(self):
        return self.root.find('application').get('{' + Manifest.URI + '}debuggable') == 'true'

    def get_sdk(self, sdk='min'):
        result = self.root.find('application').find('uses-sdk').get('{' + Manifest.URI + '}{sdk}SdkVersion'.format(sdk=sdk.capitalize())) if self.root.find('application').find('uses-sdk') else self.yml.get_sdk(sdk)
        return result if result else self.yml.get_sdk(sdk)

class YML(object):

    YML_FILE = 'apktool.yml'

    def __init__(self, fpath='.'):
        self.raw = ''
        if path.exists('{path}/{yml}'.format(path=fpath, yml=YML.YML_FILE)):
            with open('{path}/{yml}'.format(path=fpath, yml=YML.YML_FILE), 'r') as f:
                self.raw = f.read()

        self.minSDK      = self.raw.split('minSdkVersion:')[1].split('\'')[1].strip() if 'minSdkVersion' in self.raw else '-1'
        self.maxSDK      = self.raw.split('maxSdkVersion:')[1].split('\'')[1].strip() if 'maxSdkVersion' in self.raw else '-1'
        self.targetSDK   = self.raw.split('targetSdkVersion:')[1].split('\'')[1].strip() if 'targetSdkVersion' in self.raw else '-1'
        self.apkFileName = self.raw.split('apkFileName:')[1].split('\n')[0].strip() if 'apkFileName' in self.raw else settings.apkfilename
        self.version     = self.raw.split('versionName:')[1].split('\n')[0].strip() if 'versionName' in self.raw else ''

    def get_sdk(self, sdk='min'):
        return getattr(self, '{sdk}SDK'.format(sdk=sdk.lower()))

