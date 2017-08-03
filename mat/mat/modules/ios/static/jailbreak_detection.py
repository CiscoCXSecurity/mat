from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Jailbreak Detection Check'
    DESCRIPTION = 'Checks if the application implements jailbreak detection'

    ID          = 'root-detection'
    ISSUE_TITLE = 'Application Does Not Perform Jailbreak Detection'
    FINDINGS    = 'The Team found that the application did not implement jailbreak detection.'

    REGEX       = r'jailbreak|cydia'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        result[self.ANALYSIS.LOCAL_WORKING_BIN] = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))
        self.REPORT = True

        if result:
            self.ISSUE_TITLE = 'Application Performs Jailbreak Detection'
            self.FINDINGS    = 'The Team found that the application implemented jailbreak detection mechanisms:\n'
            self.DETAILS = Utils.grep_details(result, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)

