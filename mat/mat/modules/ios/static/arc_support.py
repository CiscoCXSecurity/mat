from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'ARC Support Check'
    DESCRIPTION = 'Looks at the application for automatic reference count support'

    ID          = 'arc-support'
    ISSUE_TITLE = 'Application Does Not Use ARC APIs'
    FINDINGS    = 'The Team found that the application did not use ARC APIs.'

    REGEX       = r'_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|_objc_retain|_objc_unretain|_objc_release|_objc_autorelease'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        strings_result = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))

        if not result and not strings_result:
            self.REPORT = True

