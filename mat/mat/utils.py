# python modules
from subprocess import Popen, PIPE
from os import path, remove, getenv, walk, rmdir
import traceback

# launching stuff problems
from time import sleep

# local modules
import settings

################################################################################
#    LOG FUNCTIONS
################################################################################

class Log:
    import inspect

    MAX_TAG_SIZE = 23

    @staticmethod
    def _log(t='W', TAG='', MSG=''):
        from time import gmtime, strftime
        now = strftime('%Y-%m-%d %H:%M:%S', gmtime())
        space = Log.MAX_TAG_SIZE - min(Log.MAX_TAG_SIZE, len(TAG))
        print('[{type}]({now}) {tag}{space} : {msg}'.format(now=now, tag=TAG[:Log.MAX_TAG_SIZE], space=' '*space, type=t, msg=MSG))

    @staticmethod
    def write(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('W', TAG, MSG)

    @staticmethod
    def w(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('W', TAG, MSG)

    @staticmethod
    def error(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('E', TAG, MSG)

    @staticmethod
    def e(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('E', TAG, MSG)

    @staticmethod
    def debug(MSG='', TAG=None):
        if not settings.SILENT and settings.DEBUG:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('D', TAG, MSG)

    @staticmethod
    def d(MSG='', TAG=None):
        if not settings.SILENT and settings.DEBUG:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
            Log._log('D', TAG, MSG)

################################################################################
#    GENERAL UTILS FUNCTIONS
################################################################################

class Command(object):

    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.std = ('', '')

    def run(self, shell, timeout=1):
        import threading

        def target():
            self.process = Popen(self.cmd, shell=shell, stdout=PIPE, stderr=PIPE)
            self.std = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()

        return self.std

class Utils:

    @staticmethod
    def run(cmd='', shell=False, process=False, timeout=None):
        Log.d('Running: {cmd}'.format(cmd=cmd))

        try:
            cmd = cmd if shell else cmd.split(' ')
            if process:
                return Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)

            if timeout:
                return Command(cmd).run(shell, timeout)

            return Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell).communicate()
            #p = Popen(cmd if shell else cmd.split(' '), stdout=PIPE, stderr=PIPE, shell=shell)
            #return p if process else p.communicate()
        except Exception:
            Log.d(traceback.format_exc())

        return None

    def rmtree(self, top=None):
        if not top:
            return False
        for root, dirs, files in walk(top, topdown=False):
            for name in files:
                remove(path.join(root, name))
            for name in dirs:
                rmdir(path.join(root, name))
        rmdir(top)

def die(message=''):
    if hasattr(settings, 'tcprelay_process'):
        settings.tcprelay_process.kill()

    if message:
        tag = '{module}.{function}:{line}'.format(function=Log.inspect.stack()[1][3], line=Log.inspect.stack()[1][2], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
        Log.e(message, tag)
    exit(0)

def perror(message=''):
    Log.e(message)

def methods(object):
    return [method for method in dir(object) if callable(getattr(object, method))]

################################################################################
#    ANDROID UTILS FUNCTIONS
################################################################################

class AndroidUtils(object):

    INSTALL_PATH = '/system/xbin'

    def __init__(self, adb):
        self.ADB = adb

    def clean(self):
        self.ADB.clean()

    def pull(self, file, dest):
        self.ADB.pull(file, dest)

    def push(self, file, dest):
        self.ADB.push(file, dest)

    def getAPK(self, package):
        return self.ADB.apk(package)[:-2]

    def processes(self, device, root=True):
        return self.ADB.processes(device, root)

    def has(self, package, device):
        return package in self.ADB.packagesOn(device)

    def installBusyBox(self):
        Log.w('Installing Busy Box On: {path}'.format(path=AndroidUtils.INSTALL_PATH))

        #http://android.stackexchange.com/questions/123183/how-do-i-install-dropbear-ssh-on-android
        if 'aarch64' not in self.ADB._runDevice('shell uname -a')[0]:
            Log.e('Error: Can\'t install busybox (not x64 arch), please do it manually')
            return False

        TMP_FOLDER = '/tmp/bb-bins'

        Log.d('Pushing binaries to: {device}'.format(device=self.ADB.DEVICE))
        Utils.run('{unzip} -o {bins} -d {tmp}'.format(unzip=settings.unzip, bins=settings.busybox_bins, tmp=TMP_FOLDER))

        self.ADB.makeDir('{tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))
        self.push('{tmp}/*'.format(tmp=TMP_FOLDER), '{tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))

        Log.d('Remounting /system as rw')
        self.ADB._runDevice('shell su -c mount -o remount,rw /system')

        Log.d('Moving binaries to /system/xbin')
        self.ADB._runDevice('shell su -c cp "{tmp}/bbins/*" /system/xbin/'.format(tmp=self.ADB.TMP_FOLDER))
        self.ADB._runDevice('shell su -c chown root:shell /system/xbin/*')
        self.ADB._runDevice('shell su -c chmod 755 /system/xbin/*')

        Log.d('Installing busybox and creating symlinks')
        self.ADB._runDevice('shell su -c /system/xbin/busybox --install /system/xbin')
        self.ADB._runDevice('shell su -c ln -s /system/xbin/dropbearmulti /system/xbin/dropbear')
        self.ADB._runDevice('shell su -c ln -s /system/xbin/dropbearmulti /system/xbin/dbclient')
        self.ADB._runDevice('shell su -c ln -s /system/xbin/dropbearmulti /system/xbin/ssh')
        self.ADB._runDevice('shell su -c ln -s /system/xbin/dropbearmulti /system/xbin/dropbearkey')
        self.ADB._runDevice('shell su -c ln -s /system/xbin/dropbearmulti /system/xbin/dropbearconvert')

        Log.d('Remounting /system as ro')
        self.ADB._runDevice('shell su -c mount -o remount,ro /system')

        Log.d('Removing garbage files')
        Utils.run('rm -rf {tmp}'.format(tmp=TMP_FOLDER))
        self.ADB._runDevice('shell su -c rm -rf {tmp}/bbins'.format(tmp=self.ADB.TMP_FOLDER))

        return True

    def setupSSH(self, key=None, autostart=False):
        Log.w('Setting up Dropbear on: {device}'.format(device=self.ADB.DEVICE))

        DROPBEAR_DATA = '/data/dropbear'
        DROPBEAR_SSH  = '{data}/.ssh'.format(data=DROPBEAR_DATA)
        RSA_KEY       = 'dropbear_rsa_host_key'
        DSS_KEY       = 'dropbear_dss_host_key'

        Log.d('Creating Dropbear Folders')

        if not self.ADB.exists(DROPBEAR_DATA):
            self.ADB.makeDir(DROPBEAR_DATA)
        self.ADB._runDevice('shell su -c chmod 755 {data}'.format(data=DROPBEAR_DATA))

        if key and path.exists(key):
            Log.d('Setting up authorized keys with: {key}'.format(key=key))
            if not self.ADB.exists(DROPBEAR_SSH):
                self.ADB.makeDir(DROPBEAR_SSH)
            self.ADB._runDevice('shell su -c chmod 700 {data}'.format(data=DROPBEAR_SSH))
            self.ADB.push(key, '{tmp}/authorized_keys'.format(tmp=self.ADB.TMP_FOLDER))
            self.ADB._runDevice('shell su -c mv {tmp}/authorized_keys {ssh}/authorized_keys'.format(tmp=self.ADB.TMP_FOLDER, ssh=DROPBEAR_SSH))
            self.ADB._runDevice('shell su -c chown root: {ssh}/authorized_keys'.format(ssh=DROPBEAR_SSH))
            self.ADB._runDevice('shell su -c chmod 600 {ssh}/authorized_keys'.format(ssh=DROPBEAR_SSH))

        if autostart and not self.ADB.exists('/etc/init.local.rc') or 'dropbear' not in self.ADB._runDevice('shell cat /etc/init.local.rc')[0]:
            CONTENT = '\n# start Dropbear (ssh server) service on boot\nservice sshd /system/xbin/dropbear -s\n   user  root\n   group root\n   oneshot\n'
            FILE = ''
            if self.ADB.exists('/etc/init.local.rc'):
                FILE = self.ADB._runDevice('shell su -c cat /etc/init.local.rc')[0]

            Log.d('Updating Autostart Script')
            FILE = '{file}\n{content}'.format(file=FILE, content=CONTENT)
            with open('/tmp/init.local.rc', 'w') as f:
                f.write(FILE)

            self.ADB.push('/tmp/init.local.rc', '{tmp}/init.local.rc'.format(tmp=self.ADB.TMP_FOLDER))

            Log.d('Remounting /system as rw')
            self.ADB._runDevice('shell su -c mount -o remount,rw /system')
            self.ADB._runDevice('shell su -c mv {tmp}/init.local.rc /etc/init.local.rc'.format(tmp=self.ADB.TMP_FOLDER))

            Log.d('Remounting /system as ro')
            self.ADB._runDevice('shell su -c mount -o remount,ro /system')

    def setProxy(self, ip=None, port=None):

        #http://android.stackexchange.com/questions/123183/how-do-i-install-dropbear-ssh-on-android
        #https://github.com/dpavlin/android-command-line/blob/master/adb-install-dropbear.sh
        #https://forum.xda-developers.com/showthread.php?t=1116698

        return False

    def listApps(self, silent=False):
        packages = self.ADB.packages()
        if silent: return packages

        for package in packages:
            print package

    def pullDataContent(self, package, dest):
        return self.ADB.pullDataContent(package, dest)

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

    def checkDependencies(self, dependency='full', silent=False, install=False):
        Log.d('Checking dependencies: {dep}'.format(dep=dependency))
        passed, lpassed = True, False
        """
        if 'full' in dependency or 'proxy' in dependency:
            lpassed = self.has(self.PROXY_SETTER_PACKAGE, settings.device)
            if not lpassed:
                if install:
                    self.ADB.install(settings.proxy_setter)
                    lpassed = self.has(self.PROXY_SETTER_PACKAGE, settings.device)
            passed = passed and lpassed
            if not silent: Log.w('Proxy Setter APK : {path}'.format(path=lpassed))
        """

        if 'full' in dependency or 'drozer' in dependency or 'dynamic' in dependency:
            if not settings.drozer or not path.exists(settings.drozer):
                passed = False
            if not silent: Log.w('Drozer Path      : {path}'.format(path=settings.drozer))

            lpassed = self.has(Drozer.PACKAGE, settings.device)
            if not lpassed:
                if install:
                    self.ADB.install(settings.drozer_agent)
                    lpassed = self.has(Drozer.PACKAGE, settings.device)
            passed = passed and lpassed
            if not silent: Log.w('Drozer Agent APK : {path}'.format(path=lpassed))

        if 'full' in dependency or 'adb' in dependency or 'dynamic' in dependency:
            if not settings.adb or not path.exists(settings.adb):
                passed = False
            if not silent: Log.w('ADB Path         : {path}'.format(path=settings.adb))

        if 'full' in dependency or 'android' in dependency or 'dynamic' in dependency:
            if not settings.android or not path.exists(settings.android):
                passed = False
            if not silent: Log.w('Android Path     : {path}'.format(path=settings.android))

        if 'full' in dependency or 'emulator' in dependency or 'dynamic' in dependency:
            if not settings.emulator or not path.exists(settings.emulator):
                passed = False
            if not silent: Log.w('Emulator Path    : {path}'.format(path=settings.emulator))

        if 'full' in dependency or 'apktool' in dependency or 'static' in dependency:
            if not settings.apktool or not path.exists(settings.apktool):
                passed = False
            if not silent: Log.w('Apktool Path     : {path}'.format(path=settings.apktool))

        if 'full' in dependency or 'jdcli' in dependency or 'static' in dependency:
            if not settings.jdcli or not path.exists(settings.jdcli):
                passed = False
            if not silent: Log.w('JD-Cli Path      : {path}'.format(path=settings.jdcli))

        if 'full' in dependency or 'dex2jar' in dependency or 'static' in dependency:
            if not settings.dex2jar or not path.exists(settings.dex2jar):
                passed = False
            if not silent: Log.w('Dex2jar Path     : {path}'.format(path=settings.dex2jar))

        if 'full' in dependency or 'avd' in dependency or 'dynamic' in dependency:
            if not settings.avd or settings.avd not in Utils.run('{android} list avd'.format(android=settings.android))[0]:
                passed = False
            if not silent: Log.w('AVD              : {path}'.format(path=settings.avd))

        if 'full' in dependency or 'signjar' in dependency or 'signing' in dependency:
            if not settings.signjar or not path.exists(settings.signjar):
                passed = False
            if not silent: Log.w('Sign Jar Path    : {path}'.format(path=settings.signjar))

        if 'full' in dependency or 'cert' in dependency or 'signing' in dependency:
            if not settings.cert or not path.exists(settings.cert):
                passed = False
            if not silent: Log.w('Certificate Path : {path}'.format(path=settings.cert))

        if 'full' in dependency or 'pk8' in dependency or 'signing' in dependency:
            if not settings.pk8 or not path.exists(settings.pk8):
                passed = False
            if not silent: Log.w('PK8 File Path    : {path}'.format(path=settings.pk8))

        return passed

class ADB(object):

    TMP_FOLDER  = '/sdcard/mat-tmp'
    DATA_FOLDER = '/data/data'
    APP_FOLDER  = '/data/app'

    def __init__(self, device=None, adb=None):
        self.DEVICE = device
        self.BIN    = adb

    def _run(self, command, shell=False):
        return Utils.run('{adb} {command}'.format(adb=self.BIN, command=command), shell=shell)

    def _runDevice(self, command, device=None, shell=False):
        device = device or self.DEVICE
        return self._run('-s {device} {command}'.format(device=device, command=command), shell=shell)

    def setDevice(self, device):
        self.DEVICE = device

    def startServer(self):
        self._run('start-server')

    def stopServer(self):
        self._run('stop-server')

    def makeDir(self, path):
        self._runDevice('shell su -c mkdir {path}'.format(path=path))

    def makeTempFolder(self):
        return self.makeDir(self.TMP_FOLDER)

    def list(self, path):
        return self._runDevice('shell ls {path}'.format(path=path))[0].split('\n')

    def devices(self):
        return [line.split('\t')[0] for line in filter(lambda line: line != '', self._run('devices')[0].split('\n')[1:])]

    def online(self, device):
        for d in self._run('devices')[0].split('\n'):
            if device in d and 'device' in d:
                return True
        return False

    def packagesOn(self, device):
        return [line.split('=')[1] if '=' in line else line for line in self._runDevice('shell pm list packages -f', device=device)[0].split('\r\n')[:-1]]

    def packages(self):
        return self.packagesOn(self.DEVICE)

    def installOn(self, device, apk):
        return self._runDevice('install {apk}'.format(apk=apk), device=device)

    def install(self, apk=None):
        return self.installOn(self.DEVICE, apk)

    def uninstallFrom(self, device, package):
        return self._runDevice('uninstall {package}'.format(package=package), device=device)

    def uninstall(self, package=None):
        return self.uninstallFrom(self.DEVICE, package)

    def startActivityOn(self, device, activity):
        return self._runDevice('shell am start -n {activity}'.format(activity=activity), device=device)

    def startActivity(self, activity):
        return self.startActivityOn(self.DEVICE, activity)

    def forward(self, local, remote):
        return self._runDevice('forward {local} {remote}'.format(local=local, remote=remote))

    def removeForward(self, local):
        return self._runDevice('forward --remove {local}'.format(local=local))

    def startAppOn(self, device, package):
        return self._runDevice('shell monkey -p {package} -c android.intent.category.LAUNCHER 1'.format(package=package), device=device)[0]

    def startApp(self, package=None):
        return self.startAppOn(self.DEVICE, package)

    def logcat(self, device, count):
        return self._runDevice('logcat -t 50'.format(device=device))[0]

    def unlocked(self, device):
        result = self._runDevice('shell dumpsys power | grep mHoldingDisplaySuspendBlocker', device=device, shell=True)[0]
        while 'mHolding' not in result:
            sleep(3)
            result = self._runDevice('shell dumpsys power | grep mHoldingDisplaySuspendBlocker', device=device, shell=True)[0]
        return all('true' in option.split('=', 1)[1] for option in result.split('\n')[:-1])

    def pullDataContent(self, package, dest):
        self._runDevice('shell su -c cp -r {data}/{package} {tmp}/{package}'.format(package=package, data=ADB.DATA_FOLDER, tmp=ADB.TMP_FOLDER))
        self._runDevice('pull {tmp}/{package} {data}'.format(package=package, data=dest, tmp=ADB.TMP_FOLDER))

    def pull(self, file, dest):
        self._runDevice('shell su -c cp {file} {tmp}/'.format(tmp=ADB.TMP_FOLDER, file=file))
        return self._runDevice('pull {tmp}/{file} {dest}'.format(tmp=ADB.TMP_FOLDER, dest=dest, file=file.rsplit('/', 1)[1]))

    def push(self, file, dest):
        return self._runDevice('push {file} {dest}'.format(dest=dest, file=file))

    def apk(self, package):
        package = self._runDevice('shell pm path {package}'.format(package=package))[0]
        return package.split(':', 1)[1] if package else package

    def exists(self, file):
        return 'No such file' not in self._runDevice('shell su -c ls {file}'.format(file=file))[0]

    def processes(self, device, root=True):
        return self._runDevice('shell su -c ps', device=device)[0] if root else self._runDevice('shell ps', device=device)[0]

    def clean(self):
        self._runDevice('shell su -c rm -rf {tmp}'.format(tmp=ADB.TMP_FOLDER))

class Drozer(object):

    PACKAGE       = 'com.mwr.dz'
    MAIN_ACTIVITY = '.activities.MainActivity'
    LOCAL         = 'tcp:31415'
    REMOTE        = 'tcp:31415'

    def __init__(self, adb, drozer):
        self.ADB    = adb
        self.DROZER = drozer
        self.start()

    def start(self):
        self.ADB.startActivity('{package}/{activity}'.format(package=Drozer.PACKAGE, activity=Drozer.MAIN_ACTIVITY))
        self.ADB.forward(Drozer.LOCAL, Drozer.REMOTE)

    def install(device, apk):
        return self.ADB.installOn(device, apk)
        #return Utils.run('{adb} -s {device} install {apk}'.format(adb=settings.adb, device=device, apk=settings.drozer_agent))

    def installed(self,):
        return Drozer.PACKAGE in self.ADB.packages()

    def mainActivity(self, package):
        return Drozer.info().split('\n')[1].strip().replace(package, '')

    def _run(self, command, shell=False):
        return Utils.run('{drozer} console connect -c {command}'.format(drozer=self.DROZER, command=command), shell)

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
    def parseOutput(key=None, output=None):
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

    def mainActivity(self):
        for a in self.root.find('application').findall('activity'):
            intentf = a.find('intent-filter')
            action = intentf.find('action') if intentf else None
            # needs to have != None for some reason
            if action != None and action.get('{' + Manifest.URI + '}name') == 'android.intent.action.MAIN':
                return a.get('{' + Manifest.URI + '}name').replace(settings.package, '')

    def allowsBackup(self):
        return self.root.find('application').get('{' + Manifest.URI + '}allowBackup') == 'true'

    def debuggable(self):
        return self.root.find('application').get('{' + Manifest.URI + '}debuggable') == 'true'

    def getSDK(self, sdk='min'):
        result = self.root.find('application').find('uses-sdk').get('{' + Manifest.URI + '}{sdk}SdkVersion'.format(sdk=sdk.capitalize())) if self.root.find('application').find('uses-sdk') else self.yml.getSDK(sdk)
        return result if result else self.yml.getSDK(sdk)

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

    def getSDK(self, sdk='min'):
        return getattr(self, '{sdk}SDK'.format(sdk=sdk.lower()))

################################################################################
#    IOS UTILS FUNCTIONS
################################################################################

class IOSUtils(object):

    PREF_FILE = '/private/var/preferences/SystemConfiguration/preferences.plist'

    def runOnIOS(self, cmd='', shell=False, process=False, timeout=5):
        Log.d('Running on iOS: {cmd}'.format(cmd=cmd))

        try:
            cmd = '{ssh} \'{cmd}\''.format(ssh=settings.ssh_ios, cmd=cmd) if shell else [settings.ssh_ios, cmd]
            Log.d('Full command: {cmd}'.format(cmd=cmd))

            if process:
                return Popen(cmd, stdout=PIPE, stderr=None, shell=shell)

            #result = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell).communicate()
            result = Command(cmd).run(shell, timeout)
            if result:
                result = (result[0].split('\r\n', 2)[2], result[1]) if 'password:' in result[0] else (result[0].split('\r\n', 1)[1], result[1])

            return result
        except Exception:
            Log.d(traceback.format_exc())

        return None

    def setProxy(self, ip=None, port=None):
        Log.d("Adding proxy {ip}:{port}".format(ip=ip, port=port))

        prefs = self.getPlist(self.PREF_FILE)

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
            f.write(dictToPlist(prefs))
        self.push('/tmp/preferences.plist', '/private/var/preferences/SystemConfiguration')
        self.plistToBin(self.PREF_FILE)

        if self.checkDependencies('activator', install=True):
            self.runOnIOS('activator send switch-off.com.a3tweaks.switch.wifi')
            self.runOnIOS('activator send switch-on.com.a3tweaks.switch.wifi')
            return True

        Log.e('Activator not found in the device. Please turn the WiFi off and on again manually')

    def checkDependencies(self, dependency='full', silent=False, install=False):
        Log.d('Checking dependencies: {dep}'.format(dep=dependency))
        passed = True

        if 'full' in dependency or 'connection' in dependency or 'expect' in dependency:
            if not settings.expect:
                passed = False

            if not silent: Log.w('Expect Shell : {shell}'.format(shell=settings.expect))

        if 'full' in dependency or 'connection' in dependency:
            uname = self.runOnIOS('uname -m')
            if 'Connection refused' in uname[0] or 'Connection closed' in uname[0]:
                if not silent: Log.w('Connection Check : No Connection')
                passed = False

            elif not silent: Log.w('Connection Check : Connected')

        if 'full' in dependency or 'device' in dependency:
            uname = self.runOnIOS('uname -m')[0].lower()

            if 'iphone' not in uname and 'ipad' not in uname and 'ipod' not in uname:
                passed = False

            if not silent: Log.w('Device Check : {connected}'.format(connected=uname.strip()))

        if 'full' in dependency or 'clutch' in dependency:
            clutch = self.runOnIOS('which Clutch2')[0][:-2]
            if not clutch:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.runOnIOS('apt-get -y install com.iphonecake.clutch2')
                    if not self.checkDependencies('clutch', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('Clutch : {path}'.format(path=clutch.strip()))

        if 'full' in dependency or 'ipainstaller' in dependency:
            ipainstaller = self.runOnIOS('which ipainstaller')[0][:-2]
            if not ipainstaller:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.runOnIOS('apt-get -y install com.slugrail.ipainstaller')
                    if not self.checkDependencies('ipainstaller', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('IPA Installer : {path}'.format(path=ipainstaller.strip()))

        if 'full' in dependency or 'activator' in dependency:
            activator = self.runOnIOS('which activator')[0][:-2]
            if not activator:
                if install:
                    if not silent: Log.w('Trying to install missing tools')
                    self.runOnIOS('apt-get install libactivator')
                    if not self.checkDependencies('activator', silent, False):
                        passed = False
                else:
                    passed = False

            if not silent: Log.w('Activator : {path}'.format(path=activator.strip()))

        return passed

    def install(self, ipa=None):
        if not ipa:
            return False

        if not self.checkDependencies('ipainstaller', install=True):
            die('Error: No IPA Installer installed on the device')

        if not path.exists(ipa) or not path.isfile(ipa):
            die('Error: Invalid IPA file')

        self.push(ipa, '/tmp')
        settings.ipainstaller = self.runOnIOS('which ipainstaller')[0][:-2]

        name = ipa.rsplit('/', 1)[1] if '/' in ipa else ipa
        result = self.runOnIOS('{ipai} -f -d /tmp/{ipa}'.format(ipai=settings.ipainstaller, ipa=name))[0]
        if 'Failed' in result or 'Invalid' in result:
            die('Error: Failed to install the IPA:{result}'.format(result=result.split('\r\n')[-2:-1][0]))

        if 'successfully' in result.lower():
            self.updateAppsList(False)

            Utils.run('{unzip} -o {ipa} -d /tmp/ipa'.format(unzip=settings.unzip, ipa=ipa))

            from os import listdir
            app = listdir('/tmp/ipa/Payload/').pop()

            self.plistToXML('/tmp/ipa/Payload/{app}/Info.plist'.format(app=app), False)
            with open('/tmp/ipa/Payload/{app}/Info.plist'.format(app=app), 'r') as f:
                plist = f.read()

            Utils.run('rm -rf /tmp/ipa/')

            return plistToDict(plist)['CFBundleIdentifier']

        return False

    def plistToXML(self, file=None, ios=True):
        if not file:
            return None

        if ios:
            self.runOnIOS('plutil -convert xml1 {file}'.format(file=file))
        else:
            Utils.run('plutil -convert xml1 {file}'.format(file=file))

    def plistToBin(self, file=None, ios=True):
        if not file:
            return None

        if ios:
            self.runOnIOS('plutil -convert binary1 {file}'.format(file=file))
        else:
            Utils.run('plutil -convert binary1 {file}'.format(file=file))


    def delete(self, file=None):
        if not file:
            return False

        self.runOnIOS('rm -rf {file}'.format(file=file))
        return True

    def push(self, file=None, path=None):
        if not file or not path: return False
        cmd = '{scp} {file} {path}/{end}'.format(scp=settings.scp_to_ios, file=file, path=path, end=file.split('/')[-1])
        results = Utils.run(cmd, True)

        Log.d(results[1])
        return '100%' in results[0]

    def readFile(self, file=None):
        if not file:
            return ''

        return self.runOnIOS('cat {file}'.format(file=file))[0]

    def updateAppsList(self, silent=False):
        if not silent: Log.w('Updating apps list on iOS: may take up to 15 seconds')
        self.runOnIOS('uicache', timeout=30)

    def listApps(self, silent=False):
        PATHS = ['/var/mobile/Library/MobileInstallation/LastLaunchServicesMap.plist', '/private/var/installd/Library/MobileInstallation/LastLaunchServicesMap.plist']
        for apps_file in PATHS:
            if self.fileExists(apps_file):
                text = self.readFile(apps_file)

                # check if plain text file
                if '<key>' not in text:
                    self.plistToXML(apps_file)
                    text = self.readFile(apps_file)

                apps = plistToDict(text)['User']
                if not silent:
                   for app in apps:
                        print('{app} :\n    APP: {bin}\n    DATA: {data}'.format(app=app, bin=apps[app]['Path'], data=apps[app]['Container']))
                return apps

        die('Error: Device OS not supported')

    def listAppsOld(self, silent=False):
        settings.APPS_PATH = settings.APPS_PATH_7 if self.getIOSVersion() < 8.0 else (settings.APPS_PATH_8 if self.getIOSVersion() < 9.0 else settings.APPS_PATH_9)
        apps = self.runOnIOS('ls -d {appspath}/*/*.app | cut -d"/" -f7-'.format(appspath=settings.APPS_PATH))[0]
        if 'No such file or directory' not in apps:
            settings.iosapps = apps.split('\r\n')[:-1]

            if not silent:
                for i, app in enumerate(settings.iosapps):
                    if app:
                        uuid, name,  = app.split('/')
                        print('{i}) {name}\n    UUID: {uuid}'.format(i=i, name=name, uuid=uuid))

    def getIOSVersion(self):
        cmd = 'grep -A 1 "ProductVersion" /System/Library/CoreServices/SystemVersion.plist | tail -n 1 | cut -d">" -f2 | cut -d"<" -f1';
        result = self.runOnIOS(cmd)
        return float(result[0][:3]) if result else None

    def startTCPRelay(self):
        if not hasattr(settings, 'tcprelay_process'):
            settings.tcprelay_process = Utils.run('{cmd} -t 22:2222'.format(cmd=settings.tcprelay), True, True)
            # tcprelay not working properly
            sleep(1)

    def stopTCPRelay(self):
        if hasattr(settings, 'tcprelay_process'):
            settings.tcprelay_process.kill()

    def fileExists(self, file=None):
        return 'cannot access' not in self.runOnIOS('ls {file}'.format(file=file))[0]

    def getPlist(self, file=None):
        self.plistToXML(file)
        return plistToDict(self.readFile(file))

    def getInfo(self, app=None):
        return self.getPlist('{app}/Info.plist'.format(app=app['Path'].replace(' ', '\ ')))

    def getEntitlements(self, binary=None):
        text = self.runOnIOS('ldid -e {app}'.format(app=binary))[0]
        if text.count('</plist>') > 1:
            stext = text.split('\r\n')
            text = '\r\n'.join([i for i in stext[:len(stext)/2]])
        return plistToDict(text)

    def runApp(self, app=None):
        return self.runOnIOS('open {app}'.format(app=app['CodeInfoIdentifier']))

    def pull(self, file=None, path=None):
        if not file or not path: return False
        cmd = '{scp} {file} {path}'.format(scp=settings.scp_from_ios, file=file, path=path)
        results = Utils.run(cmd, True)

        Log.d(results[1])
        return '100%' in results[0]

    def getArchs(self, binary=None):
        result = []
        if binary:
            out = self.runOnIOS('otool -hv {binary}'.format(binary=binary))[0]
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

def dictToPlist(text):
    import plistlib
    return plistlib.writePlistToString(text)

def plistToDict(text=None):
    if not text:
        return {}

    import plistlib
    return plistlib.readPlistFromString(text)
