from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Random Check'
    DESCRIPTION = 'Checks if the application uses weak random generation functions [NOT RELIABLE]'

    ID          = 'weak-random'
    ISSUE_TITLE = 'Application Generates Insecure Random Numbers'
    FINDINGS    = 'The Team found that the application generated insecure random numbers.'

    REGEX       = r'_srand|_random'

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['satic'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        matches = re.search(REGEX, symbols)
        if matches:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([match.group() for match in matches]))

