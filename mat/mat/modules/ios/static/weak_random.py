from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Random Check'
    DESCRIPTION = 'Checks if the application uses weak random generation functions [NOT RELIABLE]'

    ID          = 'weak-random'
    ISSUE_TITLE = 'Application Generates Insecure Random Numbers'
    FINDINGS    = 'The Team found that the application generated insecure random numbers.'

    REGEX       = r'srand|random'

    def run(self):
        result = Utils.grep_command('-REin "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if result:
            self.REPORT  = True

"""
    'weak-random': {
        'regex': 'srand|random',
        'ignore-case': False,
        'reverse': False,
        'title': 'Application Generates Insecure Random Numbers [USE WITH CAUTION - DOUBLE CHECK]',
        'issue-id': 'weak-random',
        'include-findings': False
    },
"""