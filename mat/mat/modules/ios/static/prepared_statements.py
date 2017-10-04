import re

from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Prepared Statements Check'
    DESCRIPTION = 'Checks if the application does not use prepared statements'

    ID          = 'prepared-statements'
    ISSUE_TITLE = 'Application Does Not Use Prepared Statements'
    FINDINGS    = 'The Team found the application used SQLite without prepared statements.'

    REGEX       = r'sqlite3_prepare|sqlite3_bind_text'

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        matches = re.search(r'sqlite', symbols)
        if matches and not re.search(self.REGEX, symbols):
            self.REPORT = True

