from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Insecure Channels Check'
    DESCRIPTION = 'Checks if the application uses SSL functions to secure encrypted communications'

    ID          = 'insecure-support'
    ISSUE_TITLE = 'Application Communicates Over Insecure Channel'
    FINDINGS    = 'The Team found that the application did not use SSL functions to secure the encrypted channels.'

    REGEX       = r'SSLSetEnabledCiphers|TLSMinimumSupportedProtocol|TLSMaximumSupportedProtocol'

    def run(self):
        result = Utils.grep_command('-REn "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if not result:
            self.REPORT = True

"""
    'insecure-channel': {
        'regex': 'SSLSetEnabledCiphers|TLSMinimumSupportedProtocol|TLSMaximumSupportedProtocol',
        'ignore-case': False,
        'reverse': True,
        'title': 'Binary Application Communicates Over Insecure Channel',
        'issue-id': 'insecure-channel',
        'include-findings': False
    },
"""