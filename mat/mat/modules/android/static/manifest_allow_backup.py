from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Application Backup Check'
    DESCRIPTION = 'Searches the manifest file for bakup tag'

    ID          = 'permits-backups'
    ISSUE_TITLE = 'Application Permits Backups'
    FINDINGS    = 'The application was found to allow backups.'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        if self.ANALYSIS.MANIFEST.allows_backup():
            self.REPORT  = True



