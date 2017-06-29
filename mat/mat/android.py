# python modules
from os import path, makedirs, walk, remove, rmdir
from subprocess import Popen
from time import sleep

# local modules
from cordova import CordovaAnalysis
from utils import Drozer, Manifest, Utils, Log, die, methods
from report import Issue
import settings


class AndroidAnalysis(object):

    LOCAL_WORKING_FOLDER      = 'android'
    LOCAL_DATA_CONTENT_FOLDER = 'data-contents'
    LOCAL_DECOMPILED_FOLDER   = 'decompiled-app'
    LOCAL_SOURCE_FOLDER       = 'src-files'

    def __init__(self, utils, adb, apk=None, package=None):
        self.au = utils

        Log.w('Creating Analysis for: {app} / {apk}'.format(apk=apk, app=package))

        self.WORKING_APK_FILE = apk
        self.PACKAGE          = package
        self.ADB              = adb

    def prepareAnalysis(self, atype='full'):
        Log.w('Preparing Android Analysis')

        if not self.au.checkDependencies(['static', 'dynamic' if 'full' in atype else 'static'], install=True, silent=True):
            Log.e('Error: Dependencies not met, run `-r` for more details')

        self.LOCAL_WORKING_FOLDER      = '{output}/{work}'.format(output=settings.output, work=AndroidAnalysis.LOCAL_WORKING_FOLDER)
        if not path.exists(self.LOCAL_WORKING_FOLDER):
            makedirs(self.LOCAL_WORKING_FOLDER)

        self.LOCAL_DATA_CONTENT_FOLDER = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DATA_CONTENT_FOLDER)
        if not path.exists(self.LOCAL_DATA_CONTENT_FOLDER):
            makedirs(self.LOCAL_DATA_CONTENT_FOLDER)

        self.LOCAL_DECOMPILED_FOLDER   = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_DECOMPILED_FOLDER)
        if not path.exists(self.LOCAL_DECOMPILED_FOLDER):
            makedirs(self.LOCAL_DECOMPILED_FOLDER)

        self.LOCAL_SOURCE_FOLDER       = '{main}/{data}'.format(main=self.LOCAL_WORKING_FOLDER, data=AndroidAnalysis.LOCAL_SOURCE_FOLDER)
        if not path.exists(self.LOCAL_SOURCE_FOLDER):
            makedirs(self.LOCAL_SOURCE_FOLDER)

        if self.WORKING_APK_FILE:
            original = self.WORKING_APK_FILE
            self.WORKING_APK_FILE = '{working}/{apk}'.format(working=self.LOCAL_WORKING_FOLDER, apk=self.WORKING_APK_FILE.rsplit('/', 1)[1])
            Utils.run('cp {oapk} {apk}'.format(oapk=original, apk=self.WORKING_APK_FILE))

            if 'static' not in atype:
                Log.w('Installing application')
                self.ADB.install(self.WORKING_APK_FILE)

        elif self.PACKAGE:
            device_apk = self.au.getAPK(self.PACKAGE)
            if not device_apk:
                die('Error: Package not found on the device')

            self.WORKING_APK_FILE = '{working}/{package}.apk'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)
            self.au.pull(device_apk, self.WORKING_APK_FILE)

        # decompile apk
        Log.w('Decompiling {apk} to {dir}'.format(apk=self.WORKING_APK_FILE, dir=self.LOCAL_DECOMPILED_FOLDER))
        Utils.run('{apktool} -q d -f {apk} -o {out}'.format(apktool=settings.apktool, apk=self.WORKING_APK_FILE, out=self.LOCAL_DECOMPILED_FOLDER))

        self.MANIFEST = Manifest(self.LOCAL_DECOMPILED_FOLDER)
        self.PACKAGE  = self.MANIFEST.package

        self.JAR_FILE = '{working}/{package}.jar'.format(working=self.LOCAL_WORKING_FOLDER, package=self.PACKAGE)
        Log.w('Converting {apk} classes to {jar}'.format(apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))
        Utils.run('{dex2jar} --force -o {jar} {apk}'.format(dex2jar=settings.dex2jar, apk=self.WORKING_APK_FILE, jar=self.JAR_FILE))

        Log.d('Extrating java classes from {jar} to {src}'.format(src=self.LOCAL_SOURCE_FOLDER, jar=self.JAR_FILE))
        Utils.run('{jdcli} {jar} -od {src}'.format(jdcli=settings.jdcli, src=self.LOCAL_SOURCE_FOLDER, jar=self.JAR_FILE))

    def cleanAnalysis(self):
        Log.w('Cleaning Android Analysis')

        if settings.uninstall:
            self.ADB.uninstall(self.PACKAGE)

        if settings.clean:
            Utils.rmtree(self.LOCAL_WORKING_FOLDER)

        self.au.clean()

    def runDynamicAnalysis(self):

        if not self.ADB.unlocked(settings.device):
            Log.w('Please unlock the device')
        while not self.ADB.unlocked(settings.device):
            sleep(5)

        # launch the app
        self.ADB.startApp(self.PACKAGE)
        sleep(5)

        self.DROZER = Drozer(adb=self.ADB, drozer=settings.drozer)

        # Drozer
        if self.DROZER.installed() and settings.drozer:

            Log.w('Drozer: Checking path traversal vulnerable providers')
            result = Drozer.parseOutput('Vulnerable Providers', self.DROZER.traversal(self.PACKAGE))
            if result and 'No vulnerable providers found.' not in result:
                issue = Issue(settings.ANDROID_ISSUES['pathtraversal']['title'], settings.ANDROID_ISSUES['pathtraversal']['issue-id'], settings.ANDROID_ISSUES['pathtraversal']['finding'], result)
                settings.results.append(issue)

            Log.w('Drozer: Checking sql injection vulnerable providers')
            output = self.DROZER.injection(self.PACKAGE)
            result = Drozer.parseOutput('Injection in Projection', output) + Drozer.parseOutput('Injection in Selection', output)
            for i in range(result.count('No vulnerabilities found.')):
                result.remove('No vulnerabilities found.')

            if result:
                issue = Issue(settings.ANDROID_ISSUES['injection']['title'], settings.ANDROID_ISSUES['injection']['issue-id'], settings.ANDROID_ISSUES['injection']['finding'], list(set(result)))
                settings.results.append(issue)

            Log.w('Drozer: Looking for secret codes')
            result = Drozer.parseOutput(self.PACKAGE, self.DROZER.codes())
            if result:
                issue = Issue(settings.ANDROID_ISSUES['secretcodes']['title'], settings.ANDROID_ISSUES['secretcodes']['issue-id'], settings.ANDROID_ISSUES['secretcodes']['finding'], result)
                settings.results.append(issue)

            Log.w('Drozer: Checking world readable data files')
            result = Drozer.parseOutput('', self.DROZER.readable(self.PACKAGE))
            if result:
                issue = Issue(settings.ANDROID_ISSUES['worldreadable']['title'], settings.ANDROID_ISSUES['worldreadable']['issue-id'], settings.ANDROID_ISSUES['worldreadable']['finding'], result)
                settings.results.append(issue)

            Log.w('Drozer: Checking world writable data files')
            result = Drozer.parseOutput('', self.DROZER.writable(self.PACKAGE))
            if result:
                issue = Issue(settings.ANDROID_ISSUES['worldwritable']['title'], settings.ANDROID_ISSUES['worldwritable']['issue-id'], settings.ANDROID_ISSUES['worldwritable']['finding'], result)
                settings.results.append(issue)

            self.DROZER.stop()

        # check root detection
        Log.w('Checking root detection')
        if self.PACKAGE in self.au.processes(settings.device):
            result = Utils.run('{grep} -aREin "root|jailb" {src} | {grep} -Ei "detect|check"'.format(grep=settings.grep, src=self.LOCAL_SOURCE_FOLDER), True)[0]

            issue = Issue(settings.ANDROID_ISSUES['root']['title'], settings.ANDROID_ISSUES['root']['issue-id'], settings.ANDROID_ISSUES['root']['finding'], self._grep_details(self._grep_results(result)))
            settings.results.append(issue)

        # check emulator detection
        if settings.avd:
            Log.w('Checking emulator detection (this may take a while)')

            # get devices
            devices = self.ADB.devices()

            # start emulator
            sleep(2)
            process = Utils.run('{emulator} -avd {avd}'.format(emulator=settings.emulator, avd=settings.avd), shell=True, process=True)
            sleep(30)

            # diff devices -> get emulator
            emulator = list(set(self.ADB.devices()) - set(devices))

            if len(emulator) == 1:
                emulator = emulator[0]
                Log.w('Waiting for {emulator}'.format(emulator=emulator))
                while not self.ADB.online(emulator):
                    sleep(5)

                if not self.ADB.unlocked(emulator):
                    Log.w('Please unlock the emulator')
                while not self.ADB.unlocked(emulator):
                    sleep(5)

                # install and run the apk in emulator
                self.ADB.installOn(emulator, self.WORKING_APK_FILE)
                self.ADB.startAppOn(emulator, self.PACKAGE)
                sleep(10)

                # check if app in ps
                if self.PACKAGE in self.au.processes(emulator, root=False):
                    issue = Issue(settings.ANDROID_ISSUES['emulator']['title'], settings.ANDROID_ISSUES['emulator']['issue-id'], settings.ANDROID_ISSUES['emulator']['finding'], '')
                    settings.results.append(issue)

                if settings.uninstall:
                    self.ADB.uninstallFrom(emulator, self.PACKAGE)

            else:
               Low.e('More than one new device detected - emulator checks not performed')

            # terminate emulator
            process.kill()
            for p in Utils.run('ps a | grep {avd}'.format(avd=settings.avd), True)[0].split('\n'):
                if 'emulator' in p and settings.avd in p:
                    pid = p.split(' ', 1)[0]
                    Utils.run('kill -9 {pid}'.format(pid=pid))

        # pull data contents
        self.au.pullDataContent(self.PACKAGE, self.LOCAL_DATA_CONTENT_FOLDER)
        shared_preferences = '{data}/{package}/shared_prefs'.format(data=self.LOCAL_DATA_CONTENT_FOLDER, package=self.PACKAGE)

        rfiles = []
        if path.exists(shared_preferences):
            for root, dirs, files in walk(shared_preferences, topdown=False):
                for name in files:
                    rfiles.append('/data/data/{package}/shared_prefs/{file}'.format(package=self.PACKAGE, file=name))

        if rfiles:
            detailed_findings = '* {details}'.format(details='\n* '.join([f for f in rfiles]))
            issue = Issue(settings.ANDROID_ISSUES['sharedpref']['title'], settings.ANDROID_ISSUES['sharedpref']['issue-id'], settings.ANDROID_ISSUES['sharedpref']['finding'], detailed_findings)
            settings.results.append(issue)

    def runManifestChecks(self):
        permissions = []
        for permission in self.MANIFEST.permissions():
            if permission in settings.ANDROID_PERMISSIONS:
                permissions.append(permission)

        if permissions:
            permissions = '* {details}'.format(details='\n* '.join(permissions))
            settings.results.append(Issue(settings.ANDROID_ISSUES['permissions']['title'], settings.ANDROID_ISSUES['permissions']['issue-id'], settings.ANDROID_ISSUES['permissions']['finding'], permissions))

        if self.MANIFEST.allowsBackup():
            settings.results.append(Issue(settings.ANDROID_ISSUES['backup']['title'], settings.ANDROID_ISSUES['backup']['issue-id'], '', ''))

        if self.MANIFEST.debuggable():
            settings.results.append(Issue(settings.ANDROID_ISSUES['debuggable']['title'], settings.ANDROID_ISSUES['debuggable']['issue-id'], '', ''))

        if self.MANIFEST.getSDK('min') < settings.minsdk:
            details = '* Minimal supported SDK version\n<code>\nminSdkVersion="{minsdk}"\n</code>'.format(minsdk=self.MANIFEST.getSDK('min'))
            settings.results.append(Issue(settings.ANDROID_ISSUES['minsdk']['title'], settings.ANDROID_ISSUES['minsdk']['issue-id'], '', details))

        if self.MANIFEST.getSDK('target') < settings.targetsdk:
            details = '* Current target SDK version\n<code>\ntargetSdkVersion="{targetsdk}"\n</code>'.format(targetsdk=self.MANIFEST.getSDK('target'))
            settings.results.append(Issue(settings.ANDROID_ISSUES['targetsdk']['title'], settings.ANDROID_ISSUES['targetsdk']['issue-id'], '', details))

        return True

    def runStaticAnalysis(self):

        for check in settings.ANDROID_ISSUES:
            issue = settings.ANDROID_ISSUES[check]

            if 'static' not in issue['type'] or 'manifest' in issue['type']:
                continue

            # if min secure sdk flag exists, check if the min supported by the application is greater and do not report if it is
            if 'min_secure_sdk' in issue and self.MANIFEST and settings.minsdk < self.MANIFEST.getSDK('min'):
                continue

            findings, regexs = {}, {}

            for r in issue['regex']:
                result = Utils.run('{grep} -aREn "{regex}" {src}'.format(grep=settings.grep, regex=r['regex'], src=self.LOCAL_SOURCE_FOLDER), True)[0]
                if result:
                    for line in result.split('\n'):
                        if not line or ':' not in line:
                            continue
                        file, no, data = line.split(':', 2)
                        if any([file.replace(self.LOCAL_SOURCE_FOLDER ,'').startswith(i['pattern']) for i in settings.IGNORE]):
                            continue

                        if file not in findings:
                            findings[file] = []
                            regexs[file] = []
                        findings[file] += [{'line': no.strip(), 'code': data.strip()}]
                        regexs[file] += [r]

            remove = []
            for file in findings:
                report = False
                for r in issue['regex']:
                    if 'report-if-found' in r and r in regexs[file]:
                        report = True
                        break

                    if 'report-if-not-found' in r and r not in regexs[file]:
                        report = True
                        break

                if not report:
                    remove += [file]

            for file in remove:
                findings.pop(file)

            if findings:
                finding = "From a static analysis of the source code of the decompiled application, the following was identified:\n"
                settings.results.append(Issue(issue['title'], issue['issue-id'], finding, self._grep_details(findings)))

        Log.w('Running Manifest Checks')
        self.runManifestChecks()

    def _grep_results(self, result):
        findings = {}
        for line in result.split('\n'):
            if not line or ':' not in line:
                continue

            f, l, d = line.split(':', 2)
            if any([f.replace(self.LOCAL_SOURCE_FOLDER ,'').startswith(i['pattern']) for i in settings.IGNORE]):
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
            details = "{details}\n\n* {file}".format(details=details, file=f.replace(self.LOCAL_SOURCE_FOLDER,''))[1:]
            findings[f].sort()
            for d in sorted(findings[f], key=lambda k: int(k['line'])):
                details = "{details}\n * Line {line}: {code}".format(details=details, line=d['line'], code=d['code'])

        return details

    def runCordovaChecks(self):
        self.cordova = CordovaAnalysis(self.LOCAL_DECOMPILED_FOLDER, data=self.LOCAL_DATA_CONTENT_FOLDER, atype='android')
        if self.cordova.found():
            self.cordova.runAnalysis()

    def runAnalysis(self, atype='full'):
        self.prepareAnalysis(atype)

        Log.w('Starting Android Analysis')
        self.runStaticAnalysis()

        if 'full' in atype or 'dynamic' in atype:
            Log.w('Starting Dynamic Analysis')
            self.runDynamicAnalysis()

        self.runCordovaChecks()

        # calculate and save md5
        md5 = Utils.run('{md5sum} {working}'.format(md5sum=settings.md5sum, working=self.WORKING_APK_FILE))[0]
        with open('{working}.md5'.format(working=self.WORKING_APK_FILE), 'w') as f:
            f.write(md5.split(' ', 1)[0].strip())

        # print app information
        Log.w('******************** Application Info ********************')
        Log.w('Package: {app}'.format(app=self.PACKAGE))
        Log.w('Version: {version}'.format(version=self.MANIFEST.version))
        Log.w('APK: {binary}'.format(binary= self.WORKING_APK_FILE))
        Log.w('MD5: {md5}'.format(md5=md5.strip().split('\n')[0]))
        Log.w('********************     End Info     ********************')

        self.cleanAnalysis()
        return True
