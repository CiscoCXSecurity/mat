from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Jailbreak Detection Check'
    DESCRIPTION = 'Checks if the application implements jailbreak detection'

    ID          = 'root-detection'
    ISSUE_TITLE = 'Application Does Not Perform Jailbreak Detection'
    FINDINGS    = 'The Team found that the application did not implement jailbreak detection.'

    REGEX       = r'jailbr|cydia'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER, ignore_case=True)
        result[self.ANALYSIS.LOCAL_WORKING_BIN] = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-iE "{regex}"'.format(regex=self.REGEX))
        if not result[self.ANALYSIS.LOCAL_WORKING_BIN]:
            result.pop(self.ANALYSIS.LOCAL_WORKING_BIN)

        self.REPORT = True

        if result:
            self.ISSUE_TITLE = 'Application Performs Jailbreak Detection'
            self.FINDINGS    = 'The Team found that the application implemented jailbreak detection mechanisms:\n'
            self.DETAILS = Utils.grep_details(result, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)

