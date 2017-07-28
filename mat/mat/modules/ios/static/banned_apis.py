from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Banned APIs Check'
    DESCRIPTION = 'Checks if the application uses banned library functions [NOT RELIABLE]'

    ID          = 'banned-apis'
    ISSUE_TITLE = 'Application Utilises Unsafe "Banned" Library Functions'
    FINDINGS    = 'The Team found that the application used banned library functions.'

    REGEX       = r'malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|wcstok|wmemcpy',

    def run(self):
        result = Utils.grep_command('-REin "{regex}" {bin} {src}'.format(regex=self.REGEX, bin=self.ANALYSIS.LOCAL_WORKING_BIN, src=self.ANALYSIS.LOCAL_CLASS_DUMP), self.ANALYSIS.LOCAL_WORKING)
        if result:
            self.REPORT  = True

"""
    'banned-apis': {
        'regex': 'malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|wcstok|wmemcpy',
        'ignore-case': False,
        'reverse': False,
        'title': 'Binary Application Utilises Unsafe "Banned" Library Functions [USE WITH CAUTION - DOUBLE CHECK]',
        'issue-id': 'banned-apis',
        'include-findings': False
    },
"""