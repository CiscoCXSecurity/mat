from utils.utils import Issue

class Issue(Issue):

    TITLE       = 'ATS Check'
    DESCRIPTION = 'Looks at the app information to check if ATS is in use and secure'

    ID          = 'insecure-ats'
    ISSUE_TITLE = 'Application Has Insecure Application Transport Security Settings'
    FINDINGS    = 'The Team found that although ATS was active, the use of `NSAllowsArbitraryLoads\' negates its effects:\n'

    def run(self):
        if ('NSAppTransportSecurity' in self.ANALYSIS.APP_INFO and 'NSAllowsArbitraryLoads' in self.ANALYSIS.APP_INFO['NSAppTransportSecurity']
            and self.ANALYSIS.APP_INFO['NSAppTransportSecurity']['NSAllowsArbitraryLoads']) or 'NSAppTransportSecurity' not in self.ANALYSIS.APP_INFO:
            self.REPORT  = True
            self.DETAILS = '\n<code>\n    <key>NSAppTransportSecurity</key>\n    <dict>\n        <key>NSAllowsArbitraryLoads</key>\n        <true/>\n    </dict>\n</code>'

            if 'NSAppTransportSecurity' not in self.ANALYSIS.APP_INFO:
                self.DETAILS  = ''
                self.FINDINGS = 'The Team found that ATS was not active on the application.'

