import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'ARC Support Check'
    DESCRIPTION = 'Looks at the application for automatic reference count support'

    ID          = 'arc-support'
    ISSUE_TITLE = 'Application Does Not Use ARC APIs'
    FINDINGS    = 'The Team found that the application did not use ARC APIs.'

    REGEX       = r'_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|_objc_retain|_objc_unretain|_objc_release|_objc_autorelease'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        symbols = self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN, self.ANALYSIS.LOCAL_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

