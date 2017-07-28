from utils.utils import Issue
from utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer Path Traversal Check'
    DESCRIPTION = 'Uses drozer to check for path traversal vulnerabilities'

    ID          = 'dir-traversal'
    ISSUE_TITLE = 'Application Has Provider Vulnerable To Directory Traversal'
    FINDINGS    = 'The Team found the following providers to be vulnerable to path traversal:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.launch_app()
        self.DROZER = Drozer(adb=self.ANALYSIS.ADB)

        result = Drozer.parse_output('Vulnerable Providers', self.DROZER.traversal(self.ANALYSIS.PACKAGE))
        if result and 'No vulnerable providers found.' not in result:
            self.DETAILS = result
            self.REPORT  = True

        self.DROZER.stop()


