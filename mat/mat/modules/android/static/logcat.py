from mat.utils.utils import Utils, Issue

IGNORE = ['www.w3', 'xmlpull.org', 'www.slf4j']

class Issue(Issue):

    TITLE       = 'Unencrypted Communications Check'
    DESCRIPTION = 'Checks if the application accesses content view unencrypted communications'

    ID          = 'unencrypted-download'
    ISSUE_TITLE = 'Application Accesses Content Via Unencrypted Channel'
    FINDINGS    = 'The Team found the application accessed the following content over unenecrypted communications:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        logs = Utils.grep(r'Log\.(w|i|v|e)\(', self.ANALYSIS.LOCAL_SOURCE)

        if logs:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(logs, self.ANALYSIS.LOCAL_SOURCE)

