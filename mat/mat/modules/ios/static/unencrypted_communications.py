from mat.utils.utils import Utils, Issue

IGNORE = ['www.w3', 'xmlpull.org', 'www.slf4j']

class Issue(Issue):

    TITLE       = 'Unencypted Communications Check'
    DESCRIPTION = 'Checks if the application communicates over unencrypted channels'

    ID          = 'unencrypted-download'
    ISSUE_TITLE = 'Application Downloads Content Via Unencrypted Channel'
    FINDINGS    = 'The Team found that the application accessed content via unencrypted channels:\n'

    REGEX       = r'http://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'], install=True)

    def run(self):
        urls = Utils.strings_grep_command(source_file=self.ANALYSIS.LOCAL_WORKING_BIN, command='-E "{regex}"'.format(regex=self.REGEX))
        result = ''
        for finding in urls:
            if any(ignore in finding['code'] for ignore in IGNORE):
                continue
            result += '* {url}\n'.format(url=finding['code'])

        if result:
            self.REPORT  = True
            self.DETAILS = result

