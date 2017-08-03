from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'WebView Javascript Bridge Check'
    DESCRIPTION = 'Checks if the application implements javascript bridges on webviews'

    ID          = 'javascript-bridge'
    ISSUE_TITLE = 'Application Utilises JavaScript Bridge Between WebView And Native Code'
    FINDINGS    = 'The Team found the application implemented javascript bridges on WebViews:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        files = Utils.grep(r'addJavascriptInterface\(|@JavascriptInterface', self.ANALYSIS.LOCAL_SOURCE)

        if files:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(files, self.ANALYSIS.LOCAL_SOURCE)

