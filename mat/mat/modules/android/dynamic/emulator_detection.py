from time import sleep
from utils.utils import Utils, Log, Issue

class Issue(Issue):

    TITLE       = 'Inadequate Detection Of Emulator Devices Check'
    DESCRIPTION = 'This module checks for emulator device detection by running the application on an emulator'

    ID          = 'emulator'
    ISSUE_TITLE = 'Application Inadequate Detects Emulator Devices'
    FINDINGS    = 'The Team identified that the application did not perform emulator detection.'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static', 'dynamic', 'avd'], install=True)

    def run(self):
        Log.w('Checking emulator detection (this may take a while)')

        # get devices
        devices = self.ANALYSIS.ADB.devices()

        # start emulator
        sleep(2)
        process = Utils.emulator()
        Log.w('Waiting for emulator to start')
        sleep(30)

        if self.ANALYSIS.UTILS.CREATED_AVD:
            Log.w('AVD just created, allowing 3 more minutes before proceeding')
            sleep(180)

        # diff devices -> get emulator
        emulator = list(set(self.ANALYSIS.ADB.devices()) - set(devices))

        if len(emulator) == 1:
            emulator = emulator[0]
            Log.w('Waiting for {emulator}'.format(emulator=emulator))
            while not self.ANALYSIS.ADB.online(emulator):
                sleep(5)

            if not self.ANALYSIS.ADB.unlocked(emulator):
                Log.w('Please unlock the emulator')
            while not self.ANALYSIS.ADB.unlocked(emulator):
                sleep(5)

            # install and run the apk in emulator
            self.ANALYSIS.ADB.install_on(emulator, self.ANALYSIS.WORKING_APK_FILE)
            self.ANALYSIS.ADB.start_app_on(emulator, self.ANALYSIS.PACKAGE)

            Log.w('Launching the app on the emulator')
            sleep(10)

            # check if app in ps
            if self.ANALYSIS.PACKAGE in self.ANALYSIS.UTILS.processes(emulator, root=False):
                self.REPORT = True

        else:
           Low.e('More than one new device detected - emulator checks not performed')

        # terminate emulator
        process.kill()

        Log.d('Checking for code that references to emulator checks')
        self.DETAILS = ''
        result = Utils.grep_command('-aRin -e "generic.*Build\.FINGERPRINT" -e "Build\.FINGERPRINT.*generic -e "sdk.*Build\.PRODUCT" -e "Build\.PRODUCT.*sdk" -e "Secure\.ANDROID_ID" -e "getSensorList" {src}'.format(src=self.ANALYSIS.LOCAL_SOURCE), self.ANALYSIS.LOCAL_SOURCE)
        if result:
            self.DETAILS += Utils.grep_details(result, self.ANALYSIS.LOCAL_SOURCE)
            self.REPORT = True