from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'WebView File Access Check'
    DESCRIPTION = 'Checks if the application disables webviews file access'

    ID          = 'webview-files'
    ISSUE_TITLE = 'Application Does Not Disable File Access On WebView Component'
    FINDINGS    = 'The Team found the application did not disable file access on WebViews:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        files = Utils.grep(r'import android\.webkit\.WebView', self.ANALYSIS.LOCAL_SOURCE) or []
        safe_files = Utils.grep(r'setAllowFileAccess\(false\)', ' '.join(list(files))) or []
        report_files = list(set(files) - set(safe_files))

        if report_files:
            self.REPORT  = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([f.replace(self.ANALYSIS.LOCAL_SOURCE, '') for f in report_files]))

