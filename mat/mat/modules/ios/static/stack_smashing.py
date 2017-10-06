import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Stack Smashing Check'
    DESCRIPTION = 'Looks at the application for stack smashing protections'

    ID          = 'stack-smashing'
    ISSUE_TITLE = 'Application Does Not Use Stack Smashing Protections'
    FINDINGS    = 'The Team found that the application did not use stack smashing protections.'

    REGEX       = r'___stack_chk_fail|___stack_chk_guard'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        symbols = self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN, self.ANALYSIS.LOCAL_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

