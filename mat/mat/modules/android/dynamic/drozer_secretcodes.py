from utils.utils import Issue
from utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer Secret Codes Search Check'
    DESCRIPTION = 'Uses drozer to check for secret codes'

    ID          = 'secret-codes'
    ISSUE_TITLE = 'Application Has Secret Codes'
    FINDINGS    = 'The Team found the following secret codes associated with application:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.launch_app()
        self.DROZER = Drozer(adb=self.ANALYSIS.ADB)

        result = Drozer.parse_output(self.ANALYSIS.PACKAGE, self.DROZER.codes())
        if result:
            self.DETAILS = result
            self.REPORT  = True

        self.DROZER.stop()


