from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Debugger Detection Check'
    DESCRIPTION = 'Checks if the application is implementing a debugger deteciton technique'

    ID          = 'debugger-detection'
    ISSUE_TITLE = 'Application Does Not Implement Debugger Detection'
    FINDINGS    = 'The Team found that the application did not check for debuggers attached to the application.'

    REGEX       = r'ptrace'

    def run(self):
        result = Utils.grep_command('-REin "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if not result:
            self.REPORT = True

"""
    'debugger-detection': {
        'regex': 'ptrace',
        'ignore-case': True,
        'reverse': True,
        'title': 'Debugger Detection Not Present',
        'issue-id': 'debugger-detection',
        'include-findings': False
    },
"""