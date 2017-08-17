# python modules
from os import path, makedirs
from time import sleep

# dynamic load modules
from os import listdir
from imp import load_source

# local modules
from cordova import CordovaAnalysis
from mat.utils.utils import Utils, Log
from mat.utils.android import Manifest
from mat.utils import settings

class AndroidAnalysis(object):
    """
        LOCAL_WORKING_FOLDER - Main folder where everything is going to be saved, usually ./mat-output

        LOCAL_DATA_CONTENT   - Folder where the data contents of the app are saved from the device

        LOCAL_DECOMPILED_APP - Folder where the app can eb found decompiled (it includes resources and smali folders)

        LOCAL_SOURCE         - Folder that contains the extracted source from the DEX files

        LOCAL_SMALI          - Folder containing the smali code for the application being analysed


        PACKAGE              - The package URI of the app being analysed

        WORKING_APK_FILE     - Path for the APK file of the app being analysed

        JAR_FILE             - JAR file extracted from the DEX file of the app


        UTILS                - Object with several methods to interact with the device and app

        MANIFEST             - Manifest object parsed from the manifest and apktool.yml files
    """

    LOCAL_WORKING_FOLDER      = 'android'
    LOCAL_DATA_CONTENT        = 'data-contents'
    LOCAL_DECOMPILED_APP      = 'decompiled-app'
    LOCAL_SOURCE              = 'src-files'

    def __init__(self, utils, apk=None, package=None):
        Log.w('Creating Analysis for: {app} / {apk}'.format(apk=apk, app=package))

        self.UTILS            = utils
        self.WORKING_APK_FILE = apk
        self.PACKAGE          = package
        self.PREPARED         = self.prepare_analysis()

    def prepare_analysis(self, decompile=True):
        Log.w('Preparing Android Analysis')

        if not self.UTILS.check_dependencies(['static', 'dynamic'], install=True, silent=True):
            Log.e('Error: Dependencies not met, run `-r` for more details')

        self.LOCAL_WORKING_FOLDER = '{output}/{work}-{uuid}'.format(output=settings.output, work=AndroidAnalysis.LOCAL_WORKING_FOLDER, uuid=(self.PACKAGE or self.WORKING_APK_FILE.rsplit('/',1)[-1].rsplit('.',1)[0]))
        self.LOCAL_DATA_CONTENT   = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DATA_CONTENT)
        self.LOCAL_DECOMPILED_APP = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DECOMPILED_APP)
        self.LOCAL_SOURCE         = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_SOURCE)
        local_paths = ['LOCAL_WORKING_FOLDER', 'LOCAL_DATA_CONTENT', 'LOCAL_DECOMPILED_APP', 'LOCAL_SOURCE']
        for local_path in local_paths:
            if not path.exists(getattr(self, local_path)):
                makedirs(getattr(self, local_path))

        if self.WORKING_APK_FILE:
            original = self.WORKING_APK_FILE
            self.WORKING_APK_FILE = '{working}/{apk}'.format(working=self.LOCAL_WORKING_FOLDER, apk=self.WORKING_APK_FILE.rsplit('/', 1)[1])
            Utils.run('cp {oapk} {apk}'.format(oapk=original, apk=self.WORKING_APK_FILE))

            if self.UTILS.device():
                Log.w('Installing application')
                self.UTILS.install(self.WORKING_APK_FILE)

        elif self.PACKAGE:
            device_apk = self.UTILS.get_apk(self.PACKAGE)
            if not device_apk:
                Log.e('Error: Package not found on the device')
                return False

            self.WORKING_APK_FILE = '{working}/{package}.apk'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)
            self.UTILS.pull(device_apk, self.WORKING_APK_FILE)

        if not self.WORKING_APK_FILE or not path.exists(self.WORKING_APK_FILE):
            Log.e('Error: Local APK file not found.')
            return False

        # decompile apk
        if decompile:
            Log.w('Decompiling {apk} to {dir}'.format(apk=self.WORKING_APK_FILE, dir=self.LOCAL_DECOMPILED_APP))
            Utils.run('{apktool} -q d -f {apk} -o {out}'.format(apktool=settings.apktool, apk=self.WORKING_APK_FILE, out=self.LOCAL_DECOMPILED_APP))

        self.MANIFEST    = Manifest(self.LOCAL_DECOMPILED_APP)
        self.PACKAGE     = self.MANIFEST.package
        self.JAR_FILE    = '{working}/{package}.jar'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)
        self.LOCAL_SMALI = '{decompiled}/smali'.format(decompiled=self.LOCAL_DECOMPILED_APP)

        if decompile:
            Log.w('Converting {apk} classes to {jar}'.format(apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))
            Utils.run('{dex2jar} --force -o {jar} {apk}'.format(dex2jar=settings.dex2jar, apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))

            Log.d('Extrating java classes from {jar} to {src}'.format(src=self.LOCAL_SOURCE, jar=self.JAR_FILE))
            Utils.run('{jdcli} {jar} -od {src}'.format(jdcli=settings.jdcli, src=self.LOCAL_SOURCE, jar=self.JAR_FILE))

        return True

    def clean_analysis(self):
        Log.w('Cleaning Android Analysis')

        if settings.uninstall:
            self.UTILS.ADB.uninstall(self.PACKAGE)

        if settings.clean:
            Utils.rmtree(self.LOCAL_WORKING_FOLDER)

    def get_custom_modules(self, modules_types=['modules/android/static', 'modules/android/dynamic']):
        found_modules = []
        for module_type in modules_types:
            modules = [m.replace('.py', '') for m in listdir('{local}/{type}'.format(local=settings.LOCAL_SETTINGS, type=module_type)) if not m.endswith('.pyc')]
            for m in modules:
                found_modules += [load_source(m, '{local}/{type}/{check}.py'.format(local=settings.LOCAL_SETTINGS, type=module_type, check=m))]
        return found_modules

    def _run_custom_modules(self, module_type):
        issues = []
        modules = self.get_custom_modules([module_type])
        for m in modules:
            Log.d('Running Static {check}'.format(check=m.__name__))
            issue = m.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        return issues

    def _run_custom_static_analysis(self):
        module_type = 'modules/android/static'
        return self._run_custom_modules(module_type)

    def _run_custom_dynamic_analysis(self):
        module_type = 'modules/android/dynamic'
        return self._run_custom_modules(module_type)

    def run_dynamic_analysis(self):
        if not self.UTILS.ADB.unlocked(settings.device):
            Log.w('Please unlock the device')
        while not self.UTILS.ADB.unlocked(settings.device):
            sleep(5)

        # launch the app
        self.UTILS.launch_app(self.PACKAGE)

        issues = []
        import mat.modules.android.dynamic
        dynamic_checks = [m.replace('.py', '') for m in listdir(mat.modules.android.dynamic.__path__[0]) if not m.endswith('.pyc') and not m.startswith('__')]
        for check in dynamic_checks:
            Log.d('Running Dynamic {check}'.format(check=check))
            check_module = __import__('mat.modules.android.dynamic.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        issues += self._run_custom_dynamic_analysis()

        return issues

    def run_static_analysis(self):
        issues = []
        import mat.modules.android.static
        static_checks = [m.replace('.py', '') for m in listdir(mat.modules.android.static.__path__[0]) if not m.endswith('.pyc') and not m.startswith('__')]
        for check in static_checks:
            Log.d('Running Static {check}'.format(check=check))
            check_module = __import__('mat.modules.android.static.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        issues += self._run_custom_static_analysis()

        return issues

    def run_cordova_checks(self):
        self.cordova = CordovaAnalysis(self.LOCAL_DECOMPILED_APP, data=self.LOCAL_DATA_CONTENT, atype='android')
        if self.cordova.found():
            return self.cordova.run_analysis()
        return []

    def run_analysis(self, atype='full'):
        if not self.PREPARED:
            Log.e('Error: Analysis not prepared')
            return []

        issues = []

        Log.w('Starting Android Analysis')
        if self.UTILS.check_dependencies(['static'], silent=True, install=False):
            issues = self.run_static_analysis()
            issues += self.run_cordova_checks()

        if ('full' in atype or 'dynamic' in atype) and self.UTILS.check_dependencies(['dynamic'], silent=True, install=False):
            Log.w('Starting Dynamic Analysis')
            issues += self.run_dynamic_analysis()

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

