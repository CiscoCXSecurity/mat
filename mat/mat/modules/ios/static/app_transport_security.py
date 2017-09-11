from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'ATS Check'
    DESCRIPTION = 'Looks at the app information to check if ATS is in use and secure'

    ID          = 'insecure-ats'
    ISSUE_TITLE = 'Application Has Insecure Application Transport Security Settings'
    FINDINGS    = 'The Team found that although ATS was active, the use of `NSAllowsArbitraryLoads\' negates its effects:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        ats = self.ANALYSIS.UTILS.dict_key_to_xml(self.ANALYSIS.APP_INFO, 'NSAppTransportSecurity')
        if 'NSAppTransportSecurity' not in self.ANALYSIS.APP_INFO:
            self.DETAILS  = ''
            self.FINDINGS = 'The Team found that ATS was not active on the application.'
            self.REPORT   = True

        elif 'NSAllowsArbitraryLoads' in ats or 'NSExceptionAllowsInsecureHTTPLoads' in ats or 'NSThirdPartyExceptionAllowsInsecureHTTPLoads' in ats:
            self.REPORT  = True
            self.DETAILS = '\n<code>\n{plist}\n</code>'.format(plist=ats)

