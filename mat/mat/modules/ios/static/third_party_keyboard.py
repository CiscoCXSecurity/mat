import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Third Party Keyboard Check'
    DESCRIPTION = 'Looks at the application checking if it blocks third party keyboards'

    ID          = '3party-keyboard'
    ISSUE_TITLE = 'Application Allows Third-Party Keyboards On Sensitive Fields'
    FINDINGS    = 'The Team found that the application did not prevent third-party keyboards from being used.'

    REGEX       = r'UIApplicationKeyboardExtensionPointIdentifier'

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

