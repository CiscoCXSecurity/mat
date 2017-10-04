import re
from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Third Party Keyboard Check'
    DESCRIPTION = 'Looks at the application checking if it blocks third party keyboards'

    ID          = '3party-keyboard'
    ISSUE_TITLE = 'Application Allows Third-Party Keyboards On Sensitive Fields'
    FINDINGS    = 'The Team found that the application did not prevent third-party keyboards from being used.'

    REGEX       = r'getInputMethodList'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        files = Utils.grep(self.REGEX, self.ANALYSIS.LOCAL_SMALI + "*")
        if not files:
            self.REPORT = True

