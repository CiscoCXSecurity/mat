from mat.utils.utils import Utils, Issue


class Issue(Issue):

    TITLE       = 'WebView Cache File Deletion Check'
    DESCRIPTION = 'Checks if the application deletes the webview cache files on exit'

    ID          = 'webview-cache'
    ISSUE_TITLE = 'Application Does Not Delete WebView Cache Files On Exit'
    FINDINGS    = 'The Team found the application did not delete WebViews\' cache files on exit:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        report_files = files = Utils.grep(r'import android\.webkit\.WebView', self.ANALYSIS.LOCAL_SOURCE) or []
        if files:
            safe_files = Utils.grep(r'clearCache\(', ' '.join(list(files))) or []
            report_files = list(set(files) - set(safe_files))

        if report_files:
            self.REPORT  = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([f.replace(self.ANALYSIS.LOCAL_SOURCE, '') for f in report_files]))

