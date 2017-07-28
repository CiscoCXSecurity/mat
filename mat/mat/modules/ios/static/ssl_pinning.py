from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'SSL Pinning Check'
    DESCRIPTION = 'Checks if the application implements ssl pinning'

    ID          = 'ssl-pinning'
    ISSUE_TITLE = 'Application Does Not Implement SSL Pinning'
    FINDINGS    = 'The Team found that the application did not implement ssl pinning.'

    REGEX       = r'setAllowInvalidCertificates|allowsInvalidSSLCertificate|validatesDomainName|SSLPinningMode'

    def run(self):
        result = Utils.grep_command('-REn "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if result:
            self.REPORT = True

"""
    'ssl-pinning': {
        'regex': 'setAllowInvalidCertificates|allowsInvalidSSLCertificate|validatesDomainName|SSLPinningMode',
        'ignore-case': False,
        'reverse': False,
        'title': 'SSL Certificate Pinning Not In Use',
        'issue-id': 'ssl-pinning',
        'include-findings': False
    },
"""