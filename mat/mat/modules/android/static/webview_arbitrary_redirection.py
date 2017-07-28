from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'WebView Arbitrary Redirection Check'
    DESCRIPTION = 'Checks if the application is vulnerable to webview arbitrary redirection'

    ID          = 'webview-redirect'
    ISSUE_TITLE = 'Application WebView Component Permits Arbitrary URL Redirection'
    FINDINGS    = 'The Team found the application was vulnerable to WebView arbitrary redirection:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        files = Utils.grep(r'import android\.webkit\.WebView', self.ANALYSIS.LOCAL_SOURCE) or []
        safe_files = Utils.grep(r'shouldOverrideUrlLoading\(', ' '.join(list(files))) or []
        report_files = list(set(files) - set(safe_files))

        if report_files:
            self.REPORT  = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([f.replace(self.ANALYSIS.LOCAL_SOURCE, '') for f in report_files]))

