import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak SSL Ciphers Check'
    DESCRIPTION = 'Checks if the application uses weak ssl ciphers'

    ID          = 'ssl-ciphers'
    ISSUE_TITLE = 'Application Uses Weak SSL Ciphers'
    FINDINGS    = 'The Team found the application used weak SSL ciphers:'

    REGEX       = r'kCFStreamSocketSecurityLevel|kSSLProtocol|kTLSProtocol|kDTLSProtocol|SSLCipherSuite'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        symbols = self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN, self.ANALYSIS.LOCAL_WORKING_BIN)
        matches = re.findall(self.REGEX, symbols)
        if matches:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(sorted(set(matches))))
