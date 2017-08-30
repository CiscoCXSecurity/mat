#system modules
from os import path, makedirs

# dynamic load modules
from os import listdir
from imp import load_source

# local modules
from cordova import CordovaAnalysis
from mat.utils.utils import Utils, Log, die
from mat.utils import settings

class IOSAnalysis(object):
    """
        LOCAL_WORKING_FOLDER - Main folder where everything is going to be saved, usually ./mat-output

        LOCAL_DATA_CONTENT   - Folder where the data contents of the app are saved from the device

        LOCAL_UNZIPED        - Folder containing the unzipped contents of the application

        LOCAL_CLASS_DUMP     - Folder containing the classes headers retreive from the application

        LOCAL_IPA            - Path to the IPA file retrieve from the file or copied from the original

        LOCAL_WORKING_BIN    - Path to the application's binary that can be analysed and modified


        APP                 - Dictionary containing information about the app on the phone: app path, data path, identifiers and app uuid

        APP_INFO            - Information about the app retrieved from Info.plist

        IOS_BIN_PATH        - Path to the binary on the device

        IOS_WORKING_BIN     - Path to the working / decrypted binary on the device


        UTILS                - Object with several methods to interact with the device and app
    """

    LOCAL_WORKING_FOLDER = 'ios'
    LOCAL_DATA_CONTENT   = 'app-data'
    LOCAL_CLASS_DUMP     = 'app-class-dump'
    LOCAL_BIN_FOLDER     = 'app-binaries'
    LOCAL_UNZIPED        = '{bins}/unziped'.format(bins=LOCAL_BIN_FOLDER)

    IOS_WORKING_FOLDER   = '/tmp/mat'
    IOS_WORKING_BIN      = None
    IOS_BIN_PATH         = None

    def __init__(self, utils, app=None, ipa=None):
        Log.w('Creating Analysis for: {app} / {ipa}'.format(app=app, ipa=ipa))

        self.UTILS    = utils
        self.IPA      = ipa
        self.APP      = app
        self.PREPARED = self.prepare_analysis()

    def prepare_analysis(self):
        Log.w('Preparing iOS Analysis')

        if not self.UTILS.check_dependencies(['full'], install=True, silent=True):
            Log.e('Error: Required dependencies not met')

        # create local output folder
        Log.d('Creating local output folders')
        self.LOCAL_WORKING_FOLDER = '{output}/{work}-{uuid}'.format(output=settings.output, work=self.LOCAL_WORKING_FOLDER, uuid=(self.APP or self.IPA.rsplit('/',1)[-1].rsplit('.',1)[0]))
        self.LOCAL_DATA_CONTENT   = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_DATA_CONTENT)
        self.LOCAL_BIN_FOLDER     = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_BIN_FOLDER)
        self.LOCAL_CLASS_DUMP     = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_CLASS_DUMP)
        self.LOCAL_UNZIPED        = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_UNZIPED)

        local_paths = ['LOCAL_WORKING_FOLDER', 'LOCAL_DATA_CONTENT', 'LOCAL_BIN_FOLDER', 'LOCAL_CLASS_DUMP']
        for local_path in local_paths:
            if not path.exists(getattr(self, local_path)):
                makedirs(getattr(self, local_path))

        if self.UTILS.check_dependencies(['connection'], silent=True):
            # create a temp folder to work with
            Log.d('Creating iOS Working folders')
            self.UTILS.run_on_ios('mkdir {working}'.format(working=self.IOS_WORKING_FOLDER))
            self.UTILS.run_on_ios('chmod 777 {working}'.format(working=self.IOS_WORKING_FOLDER))

            # push tools to the temp folder
            self.UTILS.push(settings.dump_log, self.IOS_WORKING_FOLDER)
            self.UTILS.push(settings.dump_fileprot, self.IOS_WORKING_FOLDER)
            self.UTILS.push(settings.dump_decrypt, self.IOS_WORKING_FOLDER)
            self.UTILS.push(settings.class_dump, self.IOS_WORKING_FOLDER)
            self.UTILS.push(settings.keychain_dump, self.IOS_WORKING_FOLDER)
            self.UTILS.push(settings.backup_excluded, self.IOS_WORKING_FOLDER)

            # update binary paths
            self.UTILS.DUMP_DECRYPT      = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.dump_decrypt.rsplit('/', 1)[1])
            self.UTILS.KEYCHAIN_DUMP     = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.keychain_dump.rsplit('/', 1)[1])
            self.UTILS.DUMP_FILE_PROTECT = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.dump_fileprot.rsplit('/', 1)[1])
            self.UTILS.DUMP_LOG          = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.dump_log.rsplit('/', 1)[1])
            self.UTILS.CLASS_DUMP        = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.class_dump.rsplit('/', 1)[1])
            self.UTILS.BACKUP_EXCLUDED   = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=settings.backup_excluded.rsplit('/', 1)[1])

        if self.APP: # no need to check if there's connection - it will return None if there's no connection
            apps = self.UTILS.list_apps(silent=True)
            self.APP = apps[self.APP] if self.APP in apps else None
            if not self.APP:
                Log.e("Error: The ID specified was not found in the applications list.")
                return False

        if self.IPA:
            self.LOCAL_IPA = '{binaries}/{ipa}'.format(binaries=self.LOCAL_BIN_FOLDER, ipa=self.IPA.rsplit('/', 1)[-1])
            Utils.run('cp {original} {dest}'.format(original=self.IPA, dest=self.LOCAL_IPA))

            if self.UTILS.check_dependencies(['connection'], silent=True):
                self.APP = self.UTILS.install(self.LOCAL_IPA)
                if not self.APP:
                    Log.e('Error: Couldn\'t install the app or retreive its details')
                    return False

        if not self.IPA:
            self.APP_INFO = self.UTILS.get_info(self.APP_INFO['Path'], ios=True)
            self.LOCAL_WORKING_BIN, self.LOCAL_IPA = self.UTILS.pull_ipa(self.APP, self.APP_INFO, self.LOCAL_BIN_FOLDER)

        if self.LOCAL_IPA:
            UNZIPED_APP, self.APP_INFO = self.UTILS.unzip_to(self.LOCAL_IPA, self.LOCAL_UNZIPED)
            if not hasattr(self, 'LOCAL_WORKING_BIN'):
                self.LOCAL_WORKING_BIN = '{app}/{binary}'.format(app=UNZIPED_APP, binary=self.APP_INFO['CFBundleExecutable'])

        # copy working bin to the device:
        if not hasattr(self, 'LOCAL_WORKING_BIN') and self.UTILS.check_dependencies(['connection'], silent=True):
            self.IOS_WORKING_BIN = '{working}/{binary}'.format(working=self.IOS_WORKING_FOLDER, binary=self.APP_INFO['CFBundleExecutable'])
            self.UTILS.push(self.LOCAL_WORKING_BIN, self.IOS_WORKING_FOLDER)

        if self.APP and 'Container' in self.APP:
            self.IOS_DATA_PATH = self.APP['Container'].replace(' ', '\ ')

        if self.APP and self.APP_INFO:
            self.IOS_BIN_PATH = self.UTILS.app_executable(self.APP, self.APP_INFO)

        self.LOCAL_CLASS_DUMP = '{base}/{app}'.format(base=self.LOCAL_CLASS_DUMP, app=self.APP_INFO['CFBundleExecutable'])

        # get classes
        if 'Darwin' in Utils.run('uname')[0]:
            Utils.run('{classdumpmac} -H {localbin} -o {localclassdump}'.format(classdumpmac=settings.class_dump_mac, localbin=self.LOCAL_WORKING_BIN, localclassdump=self.LOCAL_CLASS_DUMP))
        elif self.UTILS.check_dependencies(['connection'], install=False, silent=True):
            result = self.UTILS.run_on_ios('{classdump} -H "{binary}" -o {working}/app-class-dump/'.format(classdump=self.UTILS.CLASS_DUMP, binary=self.IOS_BIN_PATH, working=self.IOS_WORKING_FOLDER))
            self.UTILS.pull('{working}/app-class-dump/'.format(working=self.IOS_WORKING_FOLDER), self.LOCAL_CLASS_DUMP)

        return True and self.UTILS.check_dependencies(['full'], install=False, silent=True)

    def clean_analysis(self):
        if self.UTILS.check_dependencies(['connection'], silent=True):
            self.UTILS.delete(self.IOS_WORKING_FOLDER)

            if settings.clean:
                Utils.run('rm -rf {working}'.format(working=self.LOCAL_WORKING_FOLDER))

            if settings.ipa and settings.uninstall:
                self.UTILS.run_on_ios('{ipainstaller} -u {appid}'.format(ipainstaller=settings.ipainstaller, appid=self.APP_INFO['CFBundleIdentifier']))

    def get_custom_modules(self, modules_types=['modules/ios/static', 'modules/ios/dynamic']):
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
            else:
                Log.e('Error: Dependencies not met.')
            if issue.REPORT:
                issues += [issue]

        return issues

    def _run_custom_static_analysis(self):
        module_type = 'modules/ios/static'
        return self._run_custom_modules(module_type)

    def _run_custom_dynamic_analysis(self):
        module_type = 'modules/ios/dynamic'
        return self._run_custom_modules(module_type)

    def run_static_checks(self):
        issues = []
        import mat.modules.ios.static
        static_checks = [m.replace('.py', '') for m in listdir(mat.modules.ios.static.__path__[0]) if not m.endswith('.pyc') and not m.startswith('__')]
        for check in static_checks:
            Log.d('Running Static {check}'.format(check=check))
            check_module = __import__('mat.modules.ios.static.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            else:
                Log.e('Error: Dependencies not met.')
            if issue.REPORT:
                issues += [issue]

        issues += self._run_custom_static_analysis()

        return issues

    def run_dynamic_checks(self):
        # launch the app
        self.UTILS.launch_app(self.APP_INFO)

        issues = []
        import mat.modules.ios.dynamic
        dynamic_checks = [m.replace('.py', '') for m in listdir(mat.modules.ios.dynamic.__path__[0]) if not m.endswith('.pyc') and not m.startswith('__')]
        for check in dynamic_checks:
            Log.d('Running Dynamic {check}'.format(check=check))
            check_module = __import__('mat.modules.ios.dynamic.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            else:
                Log.e('Error: Dependencies not met.')
            if issue.REPORT:
                issues += [issue]

        issues += self._run_custom_dynamic_analysis()

        return issues

    def run_cordova_checks(self):
        self.cordova = CordovaAnalysis('{unzipped}/Payload/'.format(unzipped=self.LOCAL_UNZIPED), data=self.LOCAL_DATA_CONTENT, atype='ios')
        if self.cordova.found():
            return self.cordova.run_analysis()
        return []

    def run_analysis(self):
        if not self.PREPARED:
            Log.e('Error: Analysis not prepared')
            return []

        Log.w("Starting iOS Analysis")

        ### checks start here
        issues = self.run_static_checks()
        issues += self.run_dynamic_checks()

        ### get data from device
        Log.d('Getting data from device')
        self.UTILS.pull(self.IOS_DATA_PATH, self.LOCAL_DATA_CONTENT)

        issues += self.run_cordova_checks()

        # calculate and save md5
        md5 = Utils.run('{md5sum} {ipa}'.format(md5sum=settings.md5sum, ipa=self.LOCAL_IPA))[0]
        with open('{working}/{ipa}.md5'.format(working=self.LOCAL_BIN_FOLDER, ipa=self.IPA.rsplit('/', 1)[-1]), 'w') as f:
            f.write(md5.split(' ', 1)[0].strip())

        # print app information
        Log.w('******************** Application Info ********************')
        Log.w('Application: {app}'.format(app=self.APP_INFO['CFBundleName']))
        Log.w('Version    : {version}'.format(version=self.APP_INFO['CFBundleShortVersionString']))
        Log.w('Binary     : {binary}'.format(binary= self.APP_INFO['CFBundleExecutable']))
        Log.w('MD5        : {md5}'.format(md5=md5.strip().split('\n')[0]))
        Log.w('********************     End Info     ********************')

        self.clean_analysis()
        return issues