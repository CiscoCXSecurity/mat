from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Provider SQL Injection Check'
    DESCRIPTION = 'Checks for SQL injections on providers vulnerabilities'

    ID          = 'sql-injection'
    ISSUE_TITLE = 'Application Has Provider Vulnerable To SQL Injection'
    FINDINGS    = 'The Team identified the following providers to be vulnerable to SQL injection:\n'

    PARAMETER   = "\\'"

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        providers = self.ANALYSIS.UTILS.providers(manifest=self.ANALYSIS.MANIFEST, working_folder=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        vulnerable_providers = []
        for provider in providers:
            result = self.ANALYSIS.UTILS.query_provider(provider, projection=self.PARAMETER)
            if 'unrecognized token' in result[1]: vulnerable_providers += [provider]
            result = self.ANALYSIS.UTILS.query_provider(provider, selection=self.PARAMETER)
            if 'unrecognized token' in result[1]: vulnerable_providers += [provider]

        if vulnerable_providers:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(sorted(set(vulnerable_providers))))

            """
            bullhead:/ $ content query --uri "content://com.mwr.example.sieve.DBContentProvider/Keys/" --where "'"
            """

