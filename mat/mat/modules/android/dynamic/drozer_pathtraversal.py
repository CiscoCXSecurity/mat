from mat.utils.utils import Issue
from mat.utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer Path Traversal Check'
    DESCRIPTION = 'Uses drozer to check for path traversal vulnerabilities'

    ID          = 'dir-traversal'
    ISSUE_TITLE = 'Application Has Provider Vulnerable To Directory Traversal'
    FINDINGS    = 'The Team found the following providers to be vulnerable to path traversal:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app(self.ANALYSIS.PACKAGE)

        drozer = self.ANALYSIS.UTILS.get_drozer()
        result = Drozer.parse_output('Vulnerable Providers', drozer.traversal(self.ANALYSIS.PACKAGE))
        if result and 'No vulnerable providers found.' not in result:
            self.DETAILS = result
            self.REPORT  = True


