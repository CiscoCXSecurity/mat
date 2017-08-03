from mat.utils.utils import Issue
from mat.utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer Provider SQL Injection Check'
    DESCRIPTION = 'Uses drozer to check for SQL injections on providers vulnerabilities'

    ID          = 'sql-injection'
    ISSUE_TITLE = 'Application Has Provider Vulnerable To SQL Injection'
    FINDINGS    = 'The Team identified the following providers to be vulnerable to SQL injection:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app()

        drozer = self.ANALYSIS.UTILS.get_drozer()
        output = drozer.injection(self.ANALYSIS.PACKAGE)
        result = Drozer.parse_output('Injection in Projection', output) + Drozer.parse_output('Injection in Selection', output)
        for i in range(result.count('No vulnerabilities found.')):
            result.remove('No vulnerabilities found.')

        if result:
            self.DETAILS = list(set(result))
            self.REPORT  = True

        drozer.stop()


