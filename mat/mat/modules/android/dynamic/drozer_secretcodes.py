from mat.utils.utils import Issue
from mat.utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer Secret Codes Search Check'
    DESCRIPTION = 'Uses drozer to check for secret codes'

    ID          = 'secret-codes'
    ISSUE_TITLE = 'Application Has Secret Codes'
    FINDINGS    = 'The Team found the following secret codes associated with application:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app(self.ANALYSIS.PACKAGE)

        drozer = self.ANALYSIS.UTILS.get_drozer()
        result = Drozer.parse_output(self.ANALYSIS.PACKAGE, drozer.codes())
        if result:
            self.DETAILS = result
            self.REPORT  = True

        drozer.stop()


