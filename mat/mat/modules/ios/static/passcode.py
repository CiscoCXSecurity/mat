import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Passcode Set Check'
    DESCRIPTION = 'Checks if the application checks if the device passcode is set'

    ID          = 'passcode'
    ISSUE_TITLE = 'Application Does Not Check If Device Passcode Is Set'
    FINDINGS    = 'The Team found that the application did not check id a device passcode was set.'

    REGEX       = r'NPasscodeStatus|DeviceOwnerAuthentication'

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['satic'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

