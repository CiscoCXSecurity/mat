import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Clipboard Disable Check'
    DESCRIPTION = 'Checks if the application disables clipboard access'

    ID          = 'clipboard'
    ISSUE_TITLE = 'Application Does Not Disable Clipboard'
    FINDINGS    = 'The Team found that the application did not disable clipboard.'

    REGEX       = r'UIPasteboardNameGeneral|UIPasteboardNameFind|UIPasteboard|UIPasteboardOptionLocalOnly|UIPasteboardOptionExpirationDate'

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

