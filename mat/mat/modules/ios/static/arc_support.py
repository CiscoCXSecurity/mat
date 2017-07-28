from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'ARC Support Check'
    DESCRIPTION = 'Looks at the application for automatic reference count support'

    ID          = 'arc-support'
    ISSUE_TITLE = 'Application Does Not Use ARC APIs'
    FINDINGS    = 'The Team found that the application did not use ARC APIs.'

    REGEX       = r'_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|_objc_retain|_objc_unretain|_objc_release|_objc_autorelease'

    def run(self):
        result = Utils.grep_command('-REn "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if not result:
            self.REPORT = True

"""
    'arc-support': {
        'regex': '_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|_objc_retain|_objc_unretain|_objc_release|_objc_autorelease',
        'ignore-case': False,
        'reverse': True,
        'title': 'Application does not use ARC APIs',
        'issue-id': 'arc-support',
        'include-findings': False
    },
"""