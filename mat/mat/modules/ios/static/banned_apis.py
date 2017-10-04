from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Banned APIs Check'
    DESCRIPTION = 'Checks if the application uses banned library functions [NOT RELIABLE]'

    ID          = 'banned-apis'
    ISSUE_TITLE = 'Application Utilises Unsafe "Banned" Library Functions'
    FINDINGS    = 'The Team found that the application used banned library functions.'

    REGEX       = r'malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|wcstok|wmemcpy',

    def dependencies(self):
        return (Utils.is_osx() and self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)) or self.ANALYSIS.UTILS.check_dependencies(['dynamic'], install=True)

    def run(self):
        symbols = Utils.symbols(self.ANALYSIS.LOCAL_WORKING_BIN) if Utils.is_osx() else self.ANALYSIS.UTILS.symbols(self.ANALYSIS.IOS_WORKING_BIN)
        matches = re.search(self.REGEX, symbols)
        if matches:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join([match.group() for match in matches]))

