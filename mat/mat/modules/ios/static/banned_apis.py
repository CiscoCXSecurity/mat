from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Banned APIs Check'
    DESCRIPTION = 'Checks if the application uses banned library functions [NOT RELIABLE]'

    ID          = 'banned-apis'
    ISSUE_TITLE = 'Application Utilises Unsafe "Banned" Library Functions'
    FINDINGS    = 'The Team found that the application used banned library functions.'

    REGEX       = r'malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|wcstok|wmemcpy',

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        result[self.ANALYSIS.LOCAL_WORKING_BIN] = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))
        if not result[self.ANALYSIS.LOCAL_WORKING_BIN]:
            result.pop(self.ANALYSIS.LOCAL_WORKING_BIN)

        if result:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(result, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)

