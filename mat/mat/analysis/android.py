# python modules
from os import path, makedirs
from time import sleep

# local modules
from analysis.cordova import CordovaAnalysis
from utils.utils import Utils, Log, die
from utils.android import Manifest
from utils import settings


class AndroidAnalysis(object):

    LOCAL_WORKING_FOLDER      = 'android'
    LOCAL_DATA_CONTENT        = 'data-contents'
    LOCAL_DECOMPILED_APP      = 'decompiled-app'
    LOCAL_SOURCE              = 'src-files'

    def __init__(self, utils, adb, apk=None, package=None):
        Log.w('Creating Analysis for: {app} / {apk}'.format(apk=apk, app=package))

        self.UTILS            = utils
        self.WORKING_APK_FILE = apk
        self.PACKAGE          = package
        self.ADB              = adb

        self.launched         = False

    def launch_app(self):
        if not self.launched:
            self.launched = True
            self.ADB.start_app(self.PACKAGE) # launch the app
            sleep(5)

    def prepare_analysis(self, atype='full', decompile=True):
        Log.w('Preparing Android Analysis')

        #if not self.UTILS.check_dependencies(['static', 'dynamic' if 'full' in atype else 'static'], install=True, silent=True):
            #die('Error: Dependencies not met, run `-r` for more details')

        self.LOCAL_WORKING_FOLDER = '{output}/{work}'.format(output=settings.output, work=AndroidAnalysis.LOCAL_WORKING_FOLDER)
        if not path.exists(self.LOCAL_WORKING_FOLDER):
            makedirs(self.LOCAL_WORKING_FOLDER)

        self.LOCAL_DATA_CONTENT   = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DATA_CONTENT)
        if not path.exists(self.LOCAL_DATA_CONTENT):
            makedirs(self.LOCAL_DATA_CONTENT)

        self.LOCAL_DECOMPILED_APP = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DECOMPILED_APP)
        if not path.exists(self.LOCAL_DECOMPILED_APP):
            makedirs(self.LOCAL_DECOMPILED_APP)

        self.LOCAL_SOURCE         = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_SOURCE)
        if not path.exists(self.LOCAL_SOURCE):
            makedirs(self.LOCAL_SOURCE)

        self.LOCAL_SMALI          = '{decompiled}/smali'.format(decompiled=self.LOCAL_DECOMPILED_APP)

        if self.WORKING_APK_FILE:
            original = self.WORKING_APK_FILE
            self.WORKING_APK_FILE = '{working}/{apk}'.format(working=self.LOCAL_WORKING_FOLDER, apk=self.WORKING_APK_FILE.rsplit('/', 1)[1])
            Utils.run('cp {oapk} {apk}'.format(oapk=original, apk=self.WORKING_APK_FILE))

            if 'static' not in atype:
                Log.w('Installing application')
                self.ADB.install(self.WORKING_APK_FILE)

        elif self.PACKAGE:
            device_apk = self.UTILS.getAPK(self.PACKAGE)
            if not device_apk:
                die('Error: Package not found on the device')

            self.WORKING_APK_FILE = '{working}/{package}.apk'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)
            self.UTILS.pull(device_apk, self.WORKING_APK_FILE)

        # decompile apk
        if decompile:
            Log.w('Decompiling {apk} to {dir}'.format(apk=self.WORKING_APK_FILE, dir=self.LOCAL_DECOMPILED_APP))
            Utils.run('{apktool} -q d -f {apk} -o {out}'.format(apktool=settings.apktool, apk=self.WORKING_APK_FILE, out=self.LOCAL_DECOMPILED_APP))

        self.MANIFEST = Manifest(self.LOCAL_DECOMPILED_APP)
        self.PACKAGE  = self.MANIFEST.package

        self.JAR_FILE = '{working}/{package}.jar'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)

        if decompile:
            Log.w('Converting {apk} classes to {jar}'.format(apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))
            Utils.run('{dex2jar} --force -o {jar} {apk}'.format(dex2jar=settings.dex2jar, apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))

            Log.d('Extrating java classes from {jar} to {src}'.format(src=self.LOCAL_SOURCE, jar=self.JAR_FILE))
            Utils.run('{jdcli} {jar} -od {src}'.format(jdcli=settings.jdcli, src=self.LOCAL_SOURCE, jar=self.JAR_FILE))

    def clean_analysis(self):
        Log.w('Cleaning Android Analysis')

        if settings.uninstall:
            self.ADB.uninstall(self.PACKAGE)

        if settings.clean:
            Utils.rmtree(self.LOCAL_WORKING_FOLDER)

        self.UTILS.clean()

    def run_dynamic_analysis(self):

        if not self.ADB.unlocked(settings.device):
            Log.w('Please unlock the device')
        while not self.ADB.unlocked(settings.device):
            sleep(5)

        # launch the app
        self.launch_app()
        issues = []

        import modules.android.dynamic
        dynamic_checks = [check for check in dir(modules.android.dynamic) if not check.startswith('__') and 'import_submodules' not in check]
        for check in dynamic_checks:
            Log.d('Running Dynamic {check}'.format(check=check))
            check_module = __import__('modules.android.dynamic.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        return issues

    def run_static_analysis(self):
        issues = []

        import modules.android.static
        static_checks = [check for check in dir(modules.android.static) if not check.startswith('__') and 'import_submodules' not in check]
        for check in static_checks:
            Log.d('Running Static {check}'.format(check=check))
            check_module = __import__('modules.android.static.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        return issues

    def run_cordova_checks(self):
        self.cordova = CordovaAnalysis(self.LOCAL_DECOMPILED_APP, data=self.LOCAL_DATA_CONTENT, atype='android')
        if self.cordova.found():
            return self.cordova.run_analysis()
        return []

    def run_analysis(self, atype='full'):
        self.prepare_analysis(atype)

        Log.w('Starting Android Analysis')
        issues = self.run_static_analysis()

        if 'full' in atype or 'dynamic' in atype:
            Log.w('Starting Dynamic Analysis')
            issues += self.run_dynamic_analysis()

        issues += self.run_cordova_checks()

        # calculate and save md5
        md5 = Utils.run('{md5sum} {working}'.format(md5sum=settings.md5sum, working=self.WORKING_APK_FILE))[0]
        with open('{working}.md5'.format(working=self.WORKING_APK_FILE), 'w') as f:
            f.write(md5.split(' ', 1)[0].strip())

        # print app information
        Log.w('******************** Application Info ********************')
        Log.w('Package: {app}'.format(app=self.PACKAGE))
        Log.w('Version: {version}'.format(version=self.MANIFEST.version))
        Log.w('APK    : {binary}'.format(binary= self.WORKING_APK_FILE))
        Log.w('MD5    : {md5}'.format(md5=md5.strip().split('\n')[0]))
        Log.w('********************     End Info     ********************')

        self.clean_analysis()
        return issues

