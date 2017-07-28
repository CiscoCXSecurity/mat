from utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Out-Of-Date Cordova Version Check'
    DESCRIPTION = 'Checks if the cordova framework in use is out of date'

    ID          = 'out-of-date-cordova'
    ISSUE_TITLE = 'Application Uses Out-Of-Date Cordova Framework'
    FINDINGS    = 'The Team found the Cordova framework in used to be out of date:\n'

    def dependencies(self):
        return True

    def run(self):
        if self.ANALYSIS.CORDOVA_VERSION and self.ANALYSIS.CORDOVA_VERSION < self.ANALYSIS.LATEST_VERSION[self.ANALYSIS.ASSESSMENT_TYPE]:
            self.DETAILS = '<code>{version}</code>'.format(version=self.ANALYSIS.CORDOVA_VERSION_DETAILS)
            self.REPORT  = True

