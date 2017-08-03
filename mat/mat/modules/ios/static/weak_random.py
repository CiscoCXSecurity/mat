from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Random Check'
    DESCRIPTION = 'Checks if the application uses weak random generation functions [NOT RELIABLE]'

    ID          = 'weak-random'
    ISSUE_TITLE = 'Application Generates Insecure Random Numbers'
    FINDINGS    = 'The Team found that the application generated insecure random numbers.'

    REGEX       = r'srand|random'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        result[self.ANALYSIS.LOCAL_WORKING_BIN] = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))

        if result:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(result, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)

