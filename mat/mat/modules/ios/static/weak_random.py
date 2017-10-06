import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Random Check'
    DESCRIPTION = 'Checks if the application uses weak random generation functions [NOT RELIABLE]'

    ID          = 'weak-random'
    ISSUE_TITLE = 'Application Generates Insecure Random Numbers'
    FINDINGS    = 'The Team found that the application generated insecure random numbers.'

    REGEX       = r'_srand|_random'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        symbols = self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN, self.ANALYSIS.LOCAL_WORKING_BIN)
        matches = re.findall(self.REGEX, symbols)
        if matches:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(sorted(set(matches))))
