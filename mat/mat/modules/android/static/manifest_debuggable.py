from utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Application Debug Check'
    DESCRIPTION = 'Searches the manifest file for debuggable tag'

    ID          = 'debuggable'
    ISSUE_TITLE = 'Application Identified As Debuggable'
    FINDINGS    = 'The application was found to be set as debuggable.'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        if self.ANALYSIS.MANIFEST.debuggable():
            self.REPORT  = True



