from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Syslog Check'
    DESCRIPTION = 'Checks if the application logs to syslog'

    ID          = 'sys-log'
    ISSUE_TITLE = 'Application Logs To Console Log'
    FINDINGS    = 'The Team found that the application logged information to the console:\n'

    REGEX       = r'NSLog'

    def run(self):
        result = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))
        if result:
            self.REPORT  = True
            self.DETAILS = self.ANALYSIS.UTILS.dump_log(self.ANALYSIS.APP['CFBundleExecutable'])

