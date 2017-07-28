from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Crypto Check'
    DESCRIPTION = 'Checks if the application uses weak encryption and hashing algorithms [NOT RELIABLE]'

    ID          = 'weak-crypto'
    ISSUE_TITLE = 'Application Uses Weak Encryption and Hashing Algorithms'
    FINDINGS    = 'The Team found that the application uses weak encryption and hashing algorithms.'

    REGEX       = r'kCCAlgorithmDES|kCCAlgorithm3DES|kCCAlgorithmRC2|kCCAlgorithmRC4|kCCOptionECBMode|kCCOptionCBCMode|DES|3ES|RC2|RC4|ECB|CBC'

    def run(self):
        result = Utils.grep_command('-REin "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if result:
            self.REPORT  = True

"""
    'weak-crypto': {
        'regex': 'kCCAlgorithmDES|kCCAlgorithm3DES|kCCAlgorithmRC2|kCCAlgorithmRC4|kCCOptionECBMode|kCCOptionCBCMode|DES|3ES|RC2|RC4|ECB|CBC',
        'ignore-case': False,
        'reverse': False,
        'title': 'Weak Encryption and Hashing Algorithms',
        'issue-id': 'weak-crypto',
        'include-findings': False
    },
"""