from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Jailbreak Detection Check'
    DESCRIPTION = 'Checks if the application implements jailbreak detection'

    ID          = 'root-detection'
    ISSUE_TITLE = 'Application Does Not Perform Jailbreak Detection'
    FINDINGS    = 'The Team found that the application did not implement jailbreak detection.'

    REGEX       = r'jailbreak|cydia'

    def run(self):
        result = Utils.grep_command('-REin "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        self.REPORT = True

        if result:
            self.ISSUE_TITLE = 'Application Performs Jailbreak Detection'
            self.FINDINGS    = 'The Team found that the application implemented jailbreak detection mechanisms:\n'
            self.DETAILS     = Utils.grep_details(result)

"""
    'root-detected': {
        'title': 'Application Performs Jailbreak Detection [CHECK MANUALLY]',
        'issue-id': 'root-detection',
        'include-findings': True
    },

    'root-detection': {
        'regex': 'jailbreak|cydia',
        'ignore-case': True,
        'reverse': True,
        'title': 'Application Does Not Perform Jailbreak Detection',
        'issue-id': 'root-detection',
        'include-findings': False,
    },
"""