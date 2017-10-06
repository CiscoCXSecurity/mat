from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'PIE Support Check'
    DESCRIPTION = 'Looks at the application compilation flags for the PIE flag'

    ID          = 'pie-support'
    ISSUE_TITLE = 'Application Not Compiled With PIE'
    FINDINGS    = 'The Team found the application not to be compiled with PIE flag.\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], silent=True)

    def run(self):
        if 'PIE' not in self.ANALYSIS.UTILS.flags(self.ANALYSIS.IOS_WORKING_BIN, self.ANALYSIS.LOCAL_WORKING_BIN):
            self.REPORT  = True

