from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Path Traversal Check'
    DESCRIPTION = 'Checks for path traversal vulnerabilities'

    ID          = 'dir-traversal'
    ISSUE_TITLE = 'Application Has Provider Vulnerable To Directory Traversal'
    FINDINGS    = 'The Team found the following providers to be vulnerable to path traversal:\n'

    PATH        = '../../../../../../../../../../../../../../etc/hosts'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        providers = self.ANALYSIS.UTILS.providers(manifest=self.ANALYSIS.MANIFEST, working_folder=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        vulnerable_providers = []
        for provider in providers:
            result = self.ANALYSIS.UTILS.read_provider(provider, self.PATH)
            if result[0]: vulnerable_providers += [provider]

        if vulnerable_providers:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(vulnerable_providers))

            """
            content read --uri "content://com.mwr.example.sieve.FileBackupProvider/../../../../../../../../../../../../../../../etc/hosts"
            """

