from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Weak Crypto Check'
    DESCRIPTION = 'Checks if the application uses weak encryption and hashing algorithms [NOT RELIABLE]'

    ID          = 'weak-crypto'
    ISSUE_TITLE = 'Application Uses Weak Encryption and Hashing Algorithms'
    FINDINGS    = 'The Team found that the application uses weak encryption and hashing algorithms.'

    REGEX       = r'kCCAlgorithmDES|kCCAlgorithm3DES|kCCAlgorithmRC2|kCCAlgorithmRC4|kCCOptionECBMode|kCCOptionCBCMode|DES|3ES|RC2|RC4|ECB|CBC'

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

