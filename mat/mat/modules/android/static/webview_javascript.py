from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'WebView Javascript Enable Check'
    DESCRIPTION = 'Checks if the application enables javascript on webviews'

    ID          = 'javascript-enabled'
    ISSUE_TITLE = 'Application Enables JavaScript On WebView Component'
    FINDINGS    = 'The Team found the application enabled javascript on WebViews:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        files = Utils.grep(r'setJavaScriptEnabled\(true\)', self.ANALYSIS.LOCAL_SOURCE)

        if files:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(files, self.ANALYSIS.LOCAL_SOURCE)

