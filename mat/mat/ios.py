#system modules
from os import path, makedirs
import re

# local modules
from cordova import CordovaAnalysis
from report import Issue
from utils import Utils, Log, die
import settings

class IOSAnalysis(object):

    IOS_WORKING_FOLDER      = '/tmp/mat'
    APP                     = None
    IOSUTILS                = None
    LOCAL_WORKING_FOLDER    = 'ios'
    LOCAL_DATA_FOLDER       = 'app-data'
    LOCAL_CLASS_DUMP_FOLDER = 'app-class-dump'
    LOCAL_BIN_FOLDER        = 'app-binaries'
    LOCAL_UNZIPED_FOLDER    = '{bins}/unziped'.format(bins=LOCAL_BIN_FOLDER)

    def __init__(self, app=None, utils=None):
        if not app or not utils:
            die('Error: Missing required parameters')

        Log.w('Creating Analysis for: {app}'.format(app=app))

        self.iu = utils
        apps = self.iu.listApps(True)
        self.APP = apps[app] if app in apps else None
        if not self.APP:
            die("Error: The ID specified was not found in the applications list.")

        # set vars
        Log.d('Setting application paths')
        self.FULL_APP_PATH = self.APP['Path'].replace(' ', '\ ')
        self.APP_INFO      = self.iu.getInfo(self.APP)

        self.APP_BIN       = self.APP_INFO['CFBundleExecutable'].replace(' ', '\ ')
        self.FULL_BIN_PATH = '{apppath}/{appbin}'.format(apppath=self.FULL_APP_PATH, appbin=self.APP_BIN)
        self.DATA_PATH     = self.APP['Container'].replace(' ', '\ ')
        self.WORKING_BIN   = self.FULL_BIN_PATH.replace(' ', '\ ')

    def prepareAnalysis(self):
        Log.w('Preparing iOS Analysis')

        if not self.iu.checkDependencies(install=True, silent=True):
            Log.e('Error: Required dependencies not met')

        # create a temp folder to work with
        Log.d('Creating iOS Working folders')
        self.iu.runOnIOS('mkdir {working}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))
        self.iu.runOnIOS('chmod 777 {working}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))

        # push tools to the temp folder
        Log.d('Pushing iOS binaries')
        self.iu.push(settings.dump_log, IOSAnalysis.IOS_WORKING_FOLDER)
        self.iu.push(settings.dump_fileprot, IOSAnalysis.IOS_WORKING_FOLDER)
        self.iu.push(settings.dump_decrypt, IOSAnalysis.IOS_WORKING_FOLDER)
        self.iu.push(settings.class_dump, IOSAnalysis.IOS_WORKING_FOLDER)
        self.iu.push(settings.keychain_dump, IOSAnalysis.IOS_WORKING_FOLDER)

        # create local output folder
        Log.d('Creating local output folders')

        self.LOCAL_WORKING_FOLDER    = '{output}/{work}'.format(output=settings.output, work=self.LOCAL_WORKING_FOLDER)
        if not path.exists(self.LOCAL_WORKING_FOLDER):
            makedirs(self.LOCAL_WORKING_FOLDER)

        self.LOCAL_DATA_FOLDER       = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_DATA_FOLDER)
        if not path.exists(self.LOCAL_DATA_FOLDER):
            makedirs(self.LOCAL_DATA_FOLDER)

        self.LOCAL_BIN_FOLDER        = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_BIN_FOLDER)
        if not path.exists(self.LOCAL_BIN_FOLDER):
            makedirs(self.LOCAL_BIN_FOLDER)

        self.LOCAL_CLASS_DUMP_FOLDER = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_CLASS_DUMP_FOLDER)
        if not path.exists(self.LOCAL_CLASS_DUMP_FOLDER):
            makedirs(self.LOCAL_CLASS_DUMP_FOLDER)

        self.LOCAL_UNZIPED_FOLDER    = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=self.LOCAL_UNZIPED_FOLDER)

    def cleanAnalysis(self):
        self.iu.delete(IOSAnalysis.IOS_WORKING_FOLDER)
        if settings.clean:
            Utils.run('rm -rf {working}'.format(working=self.LOCAL_WORKING_FOLDER))

        if settings.ipa and settings.uninstall:
            self.iu.runOnIOS('{ipainstaller} -u {appid}'.format(ipainstaller=settings.ipainstaller, appid=self.APP['CodeInfoIdentifier']))

    def runAnalysis(self):
        Log.w("Starting Analysis.")

        self.prepareAnalysis()
        self.IPA = None

        settings.ipainstaller = self.iu.runOnIOS('which ipainstaller')[0][:-2]
        settings.clutch = self.iu.runOnIOS('which Clutch2')[0][:-2]

        # check if the app is encrypted and decrypt it
        Log.w('Decrypting the application')
        if 'cryptid 1' in self.iu.runOnIOS('otool -l "{binary}" | grep ENCRYPTION -B1 -A4'.format(binary=self.FULL_BIN_PATH))[0]:
            DUMP_DECRYPT = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=settings.dump_decrypt.rsplit('/', 1)[1])
            self.iu.runOnIOS('su mobile -c "cd {working}; DYLD_INSERT_LIBRARIES={dumpdecrypt} {binary}"'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, dumpdecrypt=DUMP_DECRYPT, binary=self.FULL_BIN_PATH))

            # check if .decrypted file was created
            self.WORKING_BIN = '{working}/{binary}.decrypted'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=self.APP_BIN)
            if not self.iu.fileExists(self.WORKING_BIN):
                Log.e("Error: Unable to decrypt app. Working with encrypted binary.")
                self.WORKING_BIN = self.FULL_BIN_PATH

            # Decrypt and Get the IPA file:
            Log.w('Decrypting the application to IPA. (this can take up to 30 secs)')
            result = self.iu.runOnIOS('{clutch} -n -d {app}'.format(app=self.APP['CodeInfoIdentifier'], clutch=settings.clutch), timeout=30)[0]
            if 'DONE:' in result:
                decryptedipa = result.split('DONE: ')[1].split('.ipa')[0]
                self.IPA = '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=self.APP_BIN)
                self.iu.runOnIOS('mv "{ipa}.ipa" "{newipa}"'.format(ipa=decryptedipa, newipa=self.IPA))

        if not self.IPA:
            Log.d('Application already decrypted')
            self.IPA = '{working}/{binary}.ipa'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=self.APP_BIN)
            self.iu.runOnIOS('{installer} -b {app} -o "{ipa}"'.format(installer=settings.ipainstaller, app=self.APP['CodeInfoIdentifier'], ipa=self.IPA))

        # get produced files
        Log.d('Getting binaries from device')
        self.iu.pull(self.WORKING_BIN, self.LOCAL_BIN_FOLDER)
        self.iu.pull(self.IPA, self.LOCAL_BIN_FOLDER)

        Log.d('Unzipping IPA')
        self.LOCAL_IPA = '{working}/{ipa}'.format(working=self.LOCAL_BIN_FOLDER, ipa=self.IPA.rsplit('/', 1)[1])
        Utils.run('{unzip} -o {ipa} -d {dest}'.format(unzip=settings.unzip, ipa=self.LOCAL_IPA, dest=self.LOCAL_UNZIPED_FOLDER))

        self.LOCAL_WORKING_BIN = '{path}/{bin}'.format(path=self.LOCAL_BIN_FOLDER, bin=self.WORKING_BIN.rsplit('/', 1)[1])
        archs = self.iu.getArchs(self.WORKING_BIN)

        # get classes
        if 'Darwin' not in Utils.run('uname'):
            Utils.run('{classdumpmac} -H {localbin} -o {localclassdump}'.format(classdumpmac=settings.class_dump_mac, localbin=self.LOCAL_WORKING_BIN, localclassdump=self.LOCAL_CLASS_DUMP_FOLDER))
        else:
            CLASS_DUMP = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=settings.class_dump.rsplit('/', 1)[1])
            result = self.iu.runOnIOS('{classdump} -H "{binary}" -o {working}/app-class-dump/'.format(classdump=CLASS_DUMP, binary=self.WORKING_BIN, working=IOSAnalysis.IOS_WORKING_FOLDER))
            self.iu.pull('{working}/app-class-dump/'.format(working=IOSAnalysis.IOS_WORKING_FOLDER), self.LOCAL_CLASS_DUMP_FOLDER)

        Log.w('Starting the application on the device')
        self.iu.runApp(self.APP)

        # do binary checks
        Log.w('Starting Static Checks')
        for check in settings.IOS_ISSUES:
            if 'regex' not in settings.IOS_ISSUES[check]: continue

            if 'strings' in settings.IOS_ISSUES[check] and settings.IOS_ISSUES[check]['strings']:
                result = Utils.run('{strings} {bin} | {egrep} {case} -e {regex}'.format(egrep=settings.egrep, strings=settings.strings, case='-i' if settings.IOS_ISSUES[check]['ignore-case'] else '', regex=settings.IOS_ISSUES[check]['regex'], bin=self.LOCAL_WORKING_BIN), shell=True)

            else:
                result = Utils.run('{egrep} -R{case}n -e {regex} {bin} {localclassdump}'.format(egrep=settings.egrep, case='i' if settings.IOS_ISSUES[check]['ignore-case'] else '', regex=settings.IOS_ISSUES[check]['regex'], bin=self.LOCAL_WORKING_BIN, localclassdump=self.LOCAL_CLASS_DUMP_FOLDER))

            # check if 'root-detection' and report it even if you fidn soemthing with what was found
            if 'root-detection' in check and result[0]:
                findings = '''The application seems to have jailbreak detection.
[check manually] The following data was found to be checking for jailbreak:'''
                settings.results.append(Issue(settings.IOS_ISSUES['root-detected']['title'], settings.IOS_ISSUES['root-detected']['issue-id'], findings, self._grep_details(self._grep_results(result[0]))))
                continue

            if settings.IOS_ISSUES[check]['reverse'] and not result[0]:
                settings.results.append(Issue(settings.IOS_ISSUES[check]['title'], check, ''))

            elif not settings.IOS_ISSUES[check]['reverse'] and result[0]:

                # dump log and add to finding details
                if 'log' in check:
                    DUMP_LOG = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=settings.dump_log.rsplit('/', 1)[1])
                    result = self.iu.runOnIOS('{dumplog} {app}'.format(dumplog=DUMP_LOG, app=self.APP_BIN))

                details = self._grep_details(self._grep_results(result[0])) if not 'strings' in settings.IOS_ISSUES[check] or not settings.IOS_ISSUES[check]['strings'] else result[0]
                settings.results.append(Issue(settings.IOS_ISSUES[check]['title'], settings.IOS_ISSUES[check]['issue-id'], 'The following data was found:', details if settings.IOS_ISSUES[check]['include-findings'] else ''))

        # pie check
        Log.w('Checking PIE support')
        if 'PIE' not in self.iu.runOnIOS('otool -hv {binary}'.format(binary=self.WORKING_BIN))[0]:
            settings.results.append(Issue(settings.IOS_ISSUES['pie-support']['title'], settings.IOS_ISSUES['pie-support']['issue-id'], ''))

        # file protection check
        Log.w('Checking file protection (this can take a while)')
        files = self.iu.runOnIOS('find {app} {data} -type f'.format(app=self.FULL_APP_PATH, data=self.DATA_PATH))[0].split('\r\n')
        vfiles = []
        for f in files:
            if f and (not ignoredPath(f)) and ('.' not in f or f.rsplit('.', 1)[1].strip() not in settings.IOS_IGNORED_FILE_EXT):
                DUMP_FILEP = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=settings.dump_fileprot.rsplit('/', 1)[1])
                protection = self.iu.runOnIOS('{dfp} {file}'.format(dfp=DUMP_FILEP, file=f))[0]
                if protection and 'NSFileProtectionComplete' not in protection:
                    vfiles += ['{file} ({prot})\n'.format(file=f, prot=protection.replace('\r\n', ''))]

        if vfiles:
            settings.results.append(Issue(settings.IOS_ISSUES['file-protection']['title'], settings.IOS_ISSUES['file-protection']['issue-id'], 'The following files were found to have insecure protection flags:', '* '.join(vfiles)))

        entitlements = self.iu.getEntitlements(self.FULL_BIN_PATH)

        # keychain dump
        # keys.plist, cert.plist, inet.plist, genp.plist -> ID: agrp, DATA: data
        Log.w('Checking Keychain Data')
        if 'keychain-access-groups' in entitlements:
            Log.w('Dumping keychain')

            KEYCHAIN_DUMP = '{working}/{binary}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, binary=settings.keychain_dump.rsplit('/', 1)[1])
            self.iu.runOnIOS('cd {working}; {keychain}'.format(working=IOSAnalysis.IOS_WORKING_FOLDER, keychain=KEYCHAIN_DUMP))

            keys = self.iu.getPlist('{working}/keys.plist'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))
            keys += self.iu.getPlist('{working}/genp.plist'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))
            keys += self.iu.getPlist('{working}/cert.plist'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))
            keys += self.iu.getPlist('{working}/inet.plist'.format(working=IOSAnalysis.IOS_WORKING_FOLDER))

            keychainids = entitlements['keychain-access-groups']

            data =[]
            for key in keys:
                if key['agrp'] in keychainids:
                    data += [str(key['data']) if 'data' in key else str(key)]

            if data:
                settings.results.append(Issue(settings.IOS_ISSUES['keychain-data']['title'], settings.IOS_ISSUES['keychain-data']['issue-id'], 'The following data was found in the keychain:', '<code>{data}</code>'.format(data='</code><code>'.join(data))))

        # permissions
        Log.w('Checking permissions')
        permissions = []
        if 'get-tasks-allow' in entitlements and entitlements['get-tasks-allow']:
            permissions += ['get-tasks-allow']

        for permission in settings.IOS_PERMISSIONS:
            if permission in self.APP_INFO and self.APP_INFO[permission]:
                permissions += [permission]

        if permissions:
            settings.results.append(Issue(settings.IOS_ISSUES['excessive-permissions']['title'], settings.IOS_ISSUES['excessive-permissions']['issue-id'], 'The following permissions where found:', '* {details}'.format(details='* '.join(permissions))))

        # ATS
        Log.w('Checking App Transport Security')
        if ('NSAppTransportSecurity' in self.APP_INFO and 'NSAllowsArbitraryLoads' in self.APP_INFO['NSAppTransportSecurity']
            and self.APP_INFO['NSAppTransportSecurity']['NSAllowsArbitraryLoads']) or 'NSAppTransportSecurity' not in self.APP_INFO:

            finding = 'The Team found that although ATS was active, the use of `NSAllowsArbitraryLoads\' negates its effects:'
            details = '''
<code>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</code>
            '''
            if 'NSAppTransportSecurity' not in self.APP_INFO:
                details = ''
                finding = 'The Team found that ATS was not active on the application'

            settings.results.append(Issue(settings.IOS_ISSUES['insecure-ats']['title'], settings.IOS_ISSUES['insecure-ats']['issue-id'], 'The following ATS permissions where found:', details))

        # get data from device
        Log.d('Getting data from device')
        self.iu.pull(self.DATA_PATH, self.LOCAL_DATA_FOLDER)

        self.runCordovaChecks()

        # calculate and save md5
        md5 = Utils.run('{md5sum} {ipa}'.format(md5sum=settings.md5sum, ipa=self.LOCAL_IPA))[0]
        with open('{working}/{ipa}.md5'.format(working=self.LOCAL_BIN_FOLDER, ipa=self.IPA.rsplit('/', 1)[1]), 'w') as f:
            f.write(md5.split(' ', 1)[0].strip())

        # print app information
        Log.w('******************** Application Info ********************')
        Log.w('Application: {app}'.format(app=self.APP_INFO['CFBundleName']))
        Log.w('Version: {version}'.format(version=self.APP_INFO['CFBundleShortVersionString']))
        Log.w('Binary: {binary}'.format(binary= self.APP_BIN))
        Log.w('MD5: {md5}'.format(md5=md5.strip().split('\n')[0]))
        Log.w('********************     End Info     ********************')

        self.cleanAnalysis()

    def _grep_results(self, result):
        findings = {}
        for line in result.split('\n'):
            if not line or ':' not in line:
                continue

            try:
                f, l, d = line.split(':', 2)
            except:
                print line
                continue
            if any([f.replace(self.LOCAL_CLASS_DUMP_FOLDER ,'').startswith(i['pattern']) for i in settings.IGNORE]):
                continue

            #data = 'Line {line}: {code}'.format(line=l.strip(), code=d.strip())
            data = {'line': l.strip(), 'code': d.strip()}
            if f in findings:
                findings[f].append(data)
            else:
                findings[f] = [data]

        return findings

    def _grep_details(self, findings):
        if not findings: return ""
        details = ""
        for f in findings:
            details = "{details}\n\n* {file}".format(details=details, file=f.replace(self.LOCAL_CLASS_DUMP_FOLDER,''))[1:]
            findings[f].sort()
            for d in sorted(findings[f], key=lambda k: int(k['line'])):
                details = "{details}\n * Line {line}: {code}".format(details=details, line=d['line'], code=d['code'])

        return details

    def runCordovaChecks(self):
        self.cordova = CordovaAnalysis('{unzipped}/Payload/'.format(unzipped=self.LOCAL_UNZIPED_FOLDER), data=self.LOCAL_DATA_FOLDER, atype='ios')
        if self.cordova.found():
            self.cordova.runAnalysis()

def ignoredPath(fpath=None):
    if not fpath: return False

    for p in settings.IGNORE:
        if p['path'] and p['pattern'] in fpath:
            return True

    return False
