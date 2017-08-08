from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Insecure Channels Check'
    DESCRIPTION = 'Checks if the application uses SSL functions to secure encrypted communications'

    ID          = 'insecure-channel'
    ISSUE_TITLE = 'Application Communicates Over Insecure Channel'
    FINDINGS    = 'The Team found that the application did not use SSL functions to secure the encrypted channels.'

    REGEX       = r'SSLSetEnabledCiphers|TLSMinimumSupportedProtocol|TLSMaximumSupportedProtocol'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        result = Utils.grep(regex=self.REGEX, source=self.ANALYSIS.LOCAL_CLASS_DUMP, working_path=self.ANALYSIS.LOCAL_WORKING_FOLDER)
        strings_result = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))

        if not result and not strings_result:
            self.REPORT = True

