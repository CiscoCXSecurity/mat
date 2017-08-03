from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Debugger Detection Check'
    DESCRIPTION = 'Checks if the application is implementing a debugger deteciton technique'

    ID          = 'debugger-detection'
    ISSUE_TITLE = 'Application Does Not Implement Debugger Detection'
    FINDINGS    = 'The Team found that the application did not check for debuggers attached to the application.'

    REGEX       = r'ptrace'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        strings_result = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))

        if not result and not strings_result:
            self.REPORT = True

