#system modules
from os import path, makedirs

# local modules
from analysis.cordova import CordovaAnalysis
from utils.utils import Utils, Log, die
from utils import settings

class IOSAnalysis(object):

    IOS_WORKING      = '/tmp/mat'
    APP              = None
    LOCAL_WORKING    = 'ios'
    LOCAL_DATA       = 'app-data'
    LOCAL_CLASS_DUMP = 'app-class-dump'
    LOCAL_BIN        = 'app-binaries'
    LOCAL_UNZIPED    = '{bins}/unziped'.format(bins=LOCAL_BIN)

    def __init__(self, app=None, utils=None):
        if not app or not utils:
            Log.e('Error: Missing required parameters')
            return None

        Log.w('Creating Analysis for: {app}'.format(app=app))

        self.launched = False

        self.UTILS = utils
        apps = self.UTILS.listApps(True)
        self.APP = apps[app] if app in apps else None
        if not self.APP:
            die("Error: The ID specified was not found in the applications list.")

        # set vars
        Log.d('Setting application paths')
        self.FULL_APP_PATH = self.APP['Path'].replace(' ', '\ ')
        self.APP_INFO      = self.UTILS.getInfo(self.APP)

        self.APP_BIN       = self.APP_INFO['CFBundleExecutable'].replace(' ', '\ ')
        self.FULL_BIN_PATH = '{apppath}/{appbin}'.format(apppath=self.FULL_APP_PATH, appbin=self.APP_BIN)
        self.DATA_PATH     = self.APP['Container'].replace(' ', '\ ')
        self.WORKING_BIN   = self.FULL_BIN_PATH.replace(' ', '\ ')

    def launch_app(self):
        if not self.launched:
            Log.w('Starting the application on the device')
            self.launched = True
            self.UTILS.run_app(self.APP)
            sleep(5)

    def prepare_analysis(self):
        Log.w('Preparing iOS Analysis')

        if not self.UTILS.check_dependencies(install=True, silent=True):
            Log.e('Error: Required dependencies not met')

        # create a temp folder to work with
        Log.d('Creating iOS Working folders')
        self.UTILS.run_on_ios('mkdir {working}'.format(working=IOSAnalysis.IOS_WORKING))
        self.UTILS.run_on_ios('chmod 777 {working}'.format(working=IOSAnalysis.IOS_WORKING))

        # push tools to the temp folder
        Log.d('Pushing iOS binaries')
        self.UTILS.push(settings.dump_log, IOSAnalysis.IOS_WORKING)
        self.UTILS.push(settings.dump_fileprot, IOSAnalysis.IOS_WORKING)
        self.UTILS.push(settings.dump_decrypt, IOSAnalysis.IOS_WORKING)
        self.UTILS.push(settings.class_dump, IOSAnalysis.IOS_WORKING)
        self.UTILS.push(settings.keychain_dump, IOSAnalysis.IOS_WORKING)

        # create local output folder
        Log.d('Creating local output folders')

        self.LOCAL_WORKING    = '{output}/{work}'.format(output=settings.output, work=self.LOCAL_WORKING)
        if not path.exists(self.LOCAL_WORKING):
            makedirs(self.LOCAL_WORKING)

        self.LOCAL_DATA       = '{main}/{data}'.format(main=self.LOCAL_WORKING, data=self.LOCAL_DATA)
        if not path.exists(self.LOCAL_DATA):
            makedirs(self.LOCAL_DATA)

        self.LOCAL_BIN        = '{main}/{data}'.format(main=self.LOCAL_WORKING, data=self.LOCAL_BIN)
        if not path.exists(self.LOCAL_BIN):
            makedirs(self.LOCAL_BIN)

        self.LOCAL_CLASS_DUMP = '{main}/{data}'.format(main=self.LOCAL_WORKING, data=self.LOCAL_CLASS_DUMP)
        if not path.exists(self.LOCAL_CLASS_DUMP):
            makedirs(self.LOCAL_CLASS_DUMP)

        self.LOCAL_UNZIPED    = '{main}/{data}'.format(main=self.LOCAL_WORKING, data=self.LOCAL_UNZIPED)

        self.IPA = None
        settings.ipainstaller = self.UTILS.run_on_ios('which ipainstaller')[0][:-2]
        settings.clutch = self.UTILS.run_on_ios('which Clutch2')[0][:-2]

        # check if the app is encrypted and decrypt it
        Log.w('Decrypting the application')
        if 'cryptid 1' in self.UTILS.run_on_ios('otool -l "{binary}" | grep ENCRYPTION -B1 -A4'.format(binary=self.FULL_BIN_PATH))[0]:
            DUMP_DECRYPT = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING, binary=settings.dump_decrypt.rsplit('/', 1)[1])
            self.UTILS.run_on_ios('su mobile -c "cd {working}; DYLD_INSERT_LIBRARIES={dumpdecrypt} {binary}"'.format(working=IOSAnalysis.IOS_WORKING, dumpdecrypt=DUMP_DECRYPT, binary=self.FULL_BIN_PATH))

            # check if .decrypted file was created
            self.WORKING_BIN = '{working}/{binary}.decrypted'.format(working=IOSAnalysis.IOS_WORKING, binary=self.APP_BIN)
            if not self.UTILS.fileExists(self.WORKING_BIN):
                Log.e("Error: Unable to decrypt app. Working with encrypted binary.")
                self.WORKING_BIN = self.FULL_BIN_PATH

            # Decrypt and Get the IPA file:
            Log.w('Decrypting the application to IPA. (this can take up to 30 secs)')
            result = self.UTILS.run_on_ios('{clutch} -n -d {app}'.format(app=self.APP['CodeInfoIdentifier'], clutch=settings.clutch), timeout=30)[0]
            if 'DONE:' in result:
                decryptedipa = result.split('DONE: ')[1].split('.ipa')[0]
                self.IPA = '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING, binary=self.APP_BIN)
                self.UTILS.run_on_ios('mv "{ipa}.ipa" "{newipa}"'.format(ipa=decryptedipa, newipa=self.IPA))

        if not self.IPA:
            Log.d('Application already decrypted')
            self.IPA = '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING, binary=self.APP_BIN)
            self.UTILS.run_on_ios('{installer} -b {app} -o "{ipa}"'.format(installer=settings.ipainstaller, app=self.APP['CodeInfoIdentifier'], ipa=self.IPA))

        # get produced files
        Log.d('Getting binaries from device')
        self.UTILS.pull(self.WORKING_BIN, self.LOCAL_BIN)
        self.UTILS.pull(self.IPA, self.LOCAL_BIN)

        Log.d('Unzipping IPA')
        self.LOCAL_IPA = '{working}/{ipa}'.format(working=self.LOCAL_BIN, ipa=self.IPA.rsplit('/', 1)[1])
        Utils.run('{unzip} -o {ipa} -d {dest}'.format(unzip=settings.unzip, ipa=self.LOCAL_IPA, dest=self.LOCAL_UNZIPED))

        self.LOCAL_WORKING_BIN = '{path}/{bin}'.format(path=self.LOCAL_BIN, bin=self.WORKING_BIN.rsplit('/', 1)[1])
        archs = self.UTILS.getArchs(self.WORKING_BIN)

        # get classes
        if 'Darwin' not in Utils.run('uname'):
            Utils.run('{classdumpmac} -H {localbin} -o {localclassdump}'.format(classdumpmac=settings.class_dump_mac, localbin=self.LOCAL_WORKING_BIN, localclassdump=self.LOCAL_CLASS_DUMP))
        else:
            CLASS_DUMP = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING, binary=settings.class_dump.rsplit('/', 1)[1])
            result = self.UTILS.run_on_ios('{classdump} -H "{binary}" -o {working}/app-class-dump/'.format(classdump=CLASS_DUMP, binary=self.WORKING_BIN, working=IOSAnalysis.IOS_WORKING))
            self.UTILS.pull('{working}/app-class-dump/'.format(working=IOSAnalysis.IOS_WORKING), self.LOCAL_CLASS_DUMP)

        self.UTILS.KEYCHAIN_DUMP     = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING, binary=settings.keychain_dump.rsplit('/', 1)[1])
        self.UTILS.DUMP_FILE_PROTECT = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING, binary=settings.dump_fileprot.rsplit('/', 1)[1])
        self.UTILS.DUMP_LOG          = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING, binary=settings.dump_log.rsplit('/', 1)[1])

    def clean_analysis(self):
        self.UTILS.delete(IOSAnalysis.IOS_WORKING)
        if settings.clean:
            Utils.run('rm -rf {working}'.format(working=self.LOCAL_WORKING))

        if settings.ipa and settings.uninstall:
            self.UTILS.run_on_ios('{ipainstaller} -u {appid}'.format(ipainstaller=settings.ipainstaller, appid=self.APP['CodeInfoIdentifier']))

    def run_static_checks(self):
        issues = []

        import modules.ios.static
        static_checks = [check for check in dir(modules.ios.static) if not check.startswith('__') and 'import_submodules' not in check]
        for check in static_checks:
            Log.d('Running Static {check}'.format(check=check))
            check_module = __import__('modules.ios.static.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        return issues

    def run_dynamic_checks(self):
        issues = []

        import modules.ios.dynamic
        dynamic_checks = [check for check in dir(modules.ios.dynamic) if not check.startswith('__') and 'import_submodules' not in check]
        for check in dynamic_checks:
            Log.d('Running Dynamic {check}'.format(check=check))
            check_module = __import__('modules.ios.dynamic.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            if issue.REPORT:
                issues += [issue]

        return issues

    def run_cordova_hecks(self):
        self.cordova = CordovaAnalysis('{unzipped}/Payload/'.format(unzipped=self.LOCAL_UNZIPED), data=self.LOCAL_DATA, atype='ios')
        if self.cordova.found():
            self.cordova.run_analysis()

    def run_analysis(self):
        Log.w("Starting Analysis.")

        self.prepare_analysis()

        ### checks start here
        self.run_static_checks()
        self.run_dynamic_checks()

        # get data from device
        Log.d('Getting data from device')
        self.UTILS.pull(self.DATA_PATH, self.LOCAL_DATA)

        self.run_cordova_checks()

        # calculate and save md5
        md5 = Utils.run('{md5sum} {ipa}'.format(md5sum=settings.md5sum, ipa=self.LOCAL_IPA))[0]
        with open('{working}/{ipa}.md5'.format(working=self.LOCAL_BIN, ipa=self.IPA.rsplit('/', 1)[1]), 'w') as f:
            f.write(md5.split(' ', 1)[0].strip())

        # print app information
        Log.w('******************** Application Info ********************')
        Log.w('Application: {app}'.format(app=self.APP_INFO['CFBundleName']))
        Log.w('Version    : {version}'.format(version=self.APP_INFO['CFBundleShortVersionString']))
        Log.w('Binary     : {binary}'.format(binary= self.APP_BIN))
        Log.w('MD5        : {md5}'.format(md5=md5.strip().split('\n')[0]))
        Log.w('********************     End Info     ********************')

        self.clean_analysis()

