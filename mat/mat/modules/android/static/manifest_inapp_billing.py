from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Use of InApp Billing Check'
    DESCRIPTION = 'Searches the Manifest file for INAPP Biling permission'

    ID          = 'inappbilling-permission'
    ISSUE_TITLE = 'Application Uses InApp Billing Permission'
    FINDINGS    = 'The following permission was found in the Android Manifest:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        if "com.android.vending.BILLING" in self.ANALYSIS.MANIFEST.permissions():
            self.DETAILS = '* {com.android.vending.BILLING}'
            self.REPORT  = True
