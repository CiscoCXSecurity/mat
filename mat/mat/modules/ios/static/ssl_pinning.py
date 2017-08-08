from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'SSL Pinning Check'
    DESCRIPTION = 'Checks if the application implements ssl pinning'

    ID          = 'ssl-pinning'
    ISSUE_TITLE = 'Application Does Not Implement SSL Pinning'
    FINDINGS    = 'The Team found that the application did not implement ssl pinning.'

    REGEX       = r'setAllowInvalidCertificates|allowsInvalidSSLCertificate|validatesDomainName|SSLPinningMode'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        result[self.ANALYSIS.LOCAL_WORKING_BIN] = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))
        if not result[self.ANALYSIS.LOCAL_WORKING_BIN]:
            result.pop(self.ANALYSIS.LOCAL_WORKING_BIN)

        if result:
            self.REPORT = True

