from utils.utils import Issue

class Issue(Issue):

    TITLE       = 'PIE Support Check'
    DESCRIPTION = 'Looks at the application compilation flags for the PIE flag'

    ID          = 'pie-support'
    ISSUE_TITLE = 'Application Not Compiled With PIE'
    FINDINGS    = 'The Team found the application not to be compiled with PIE flag.\n'

    def run(self):
        if 'PIE' not in self.ANALYSIS.UTILS.run_on_ios('otool -hv {binary}'.format(binary=self.ANALYSIS.WORKING_BIN))[0]:
            self.REPORT  = True

