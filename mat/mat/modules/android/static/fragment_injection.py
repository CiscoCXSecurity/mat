from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Fragment Injection Check'
    DESCRIPTION = 'Checks if the application is vulnerable to fragment injection'

    ID          = 'fragment-injection'
    ISSUE_TITLE = 'Application Vulnerable To Fragment Injection'
    FINDINGS    = 'The Team found the application was vulnerable to fragment injection:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        activities = Utils.grep(r'extends PreferenceActivity', self.ANALYSIS.LOCAL_SOURCE)

        if activities and self.ANALYSIS.MANIFEST.get_sdk('min') < '18':
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(activities, self.ANALYSIS.LOCAL_SOURCE)

