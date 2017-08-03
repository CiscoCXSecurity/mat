from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Out-Of-Date Cordova Version Check'
    DESCRIPTION = 'Checks if the cordova framework in use is out of date'

    ID          = 'out-of-date-cordova'
    ISSUE_TITLE = 'Application Uses Out-Of-Date Cordova Framework'
    FINDINGS    = 'The Team found the Cordova framework in used to be out of date:\n'

    def dependencies(self):
        return True

    def run(self):
        CORDOVA_VERSION = CORDOVA_VERSION_DETAILS = None
        if self.ANALYSIS.CORDOVA_FILE:
            with open(self.CORDOVA_FILE, 'r') as f:
                cordova = f.read()

            for line in cordova.split('\n'):
                if ('CORDOVA_JS_BUILD_LABEL' in line or 'PLATFORM_VERSION_BUILD_LABEL' in line) and '\'' in line:
                    CORDOVA_VERSION = line.split('\'')[1].strip()
                    CORDOVA_VERSION_DETAILS = line

        if CORDOVA_VERSION and CORDOVA_VERSION < self.ANALYSIS.LATEST_VERSION[self.ANALYSIS.ASSESSMENT_TYPE]:
            self.DETAILS = '<code>{version}</code>'.format(version=CORDOVA_VERSION_DETAILS)
            self.REPORT  = True

