from utils.utils import Utils, Issue

IGNORE = ['www.w3', 'xmlpull.org', 'www.slf4j']

class Issue(Issue):

    TITLE       = 'Unencypted Communications Check'
    DESCRIPTION = 'Checks if the application communicates over unencrypted channels'

    ID          = 'unencrypted-download'
    ISSUE_TITLE = 'Application Downloads Content Via Unencrypted Channel'
    FINDINGS    = 'The Team found that the application accessed content via unencrypted channels:\n'

    REGEX       = r'http://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?'

    def run(self):
        urls = Utils.strings_grep_command(src=self.ANALYSIS.LOCAL_WORKING_BIN, command='-REn "{regex}"'.format(regex=self.REGEX))
        result = ''
        for finding in urls.split('\n'):
            if any(ignore in finding for ignore in IGNORE):
                continue
            result += finding + '\n'

        if result:
            self.REPORT  = True
            self.DETAILS = result

"""
    'unencrypted-download' : {
        'title': 'Application Downloads Content Via Unencrypted Channel',
        'issue-id': 'unencrypted-download',
        'regex': 'http://',
        'ignore-case': False,
        'reverse': False,
        'strings': True,
        'include-findings': True
    },
"""