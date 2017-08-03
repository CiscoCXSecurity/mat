from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Root Detection Check'
    DESCRIPTION = 'Runs several tests to determine if the application is checking for rooted devices'

    ID          = 'root-detection'
    ISSUE_TITLE = 'Application Does Not Perform Root Detection'
    FINDINGS    = 'The Team identified that the application did not perform root detection.\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static', 'dynamic'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app()
        if self.ANALYSIS.PACKAGE in self.ANALYSIS.UTILS.processes():
            self.REPORT = True

        result = Utils.multiple_grep('-aREin "root|jailb" {src}'.format(src=self.ANALYSIS.LOCAL_SOURCE), '-Ei "detect|check"')
        if result:
            self.REPORT      = True
            self.ISSUE_TITLE = 'Application Performs Root Detection'
            self.FINDINGS    = 'The Team observed that the application did performe some type fo root detection:\n'
            self.DETAILS     = Utils.grep_details(result, self.ANALYSIS.LOCAL_SOURCE)

