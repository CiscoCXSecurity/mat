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
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['satic'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        if not re.search(REGEX, symbols):
            self.REPORT = True

