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
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['satic'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        matches = re.search(self.REGEX, symbols)
        if matches:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([match.group() for match in matches]))