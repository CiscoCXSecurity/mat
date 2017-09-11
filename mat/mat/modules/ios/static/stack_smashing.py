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
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['satic'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        #result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        #strings_result = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))

        #if not result and not strings_result:
            #self.REPORT = True

        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        if not re.search(self.REGEX, symbols):
            self.REPORT = True

