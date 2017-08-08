from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Root Detection Check'
    DESCRIPTION = 'Runs several tests to determine if the application is checking for rooted devices'

    ID          = 'root-detection'
    ISSUE_TITLE = 'Application Does Not Perform Root Detection'
    FINDINGS    = 'The Team identified that the application did not perform root detection.\n'

    REGEX = r'rootdetect|rootcheck|jailb[a-zA-Z0-9_-]*|rooted|substrate|busybox|c3Vic3RyYXRl|YnVzeWJveA==|eHBvc2Vk|c3VwZXJzdQ=='

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static', 'dynamic'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app(self.ANALYSIS.PACKAGE)
        if self.ANALYSIS.PACKAGE in self.ANALYSIS.UTILS.processes():
            self.REPORT = True

        result = Utils.grep(self.REGEX, source=self.ANALYSIS.LOCAL_SOURCE, ignore_case=True)
        if result:
            self.REPORT      = True
            self.ISSUE_TITLE = 'Application Performs Root Detection'
            self.FINDINGS    = 'The Team observed that the application did performe some type fo root detection:\n'
            self.DETAILS     = Utils.grep_details(result, self.ANALYSIS.LOCAL_SOURCE)

