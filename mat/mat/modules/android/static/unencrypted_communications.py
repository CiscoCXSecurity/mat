from mat.utils.utils import Utils, Issue

IGNORE = ['www.w3', 'xmlpull.org', 'www.slf4j']

class Issue(Issue):

    TITLE       = 'Unencrypted Communications Check'
    DESCRIPTION = 'Checks if the application accesses content view unencrypted communications'

    ID          = 'unencrypted-download'
    ISSUE_TITLE = 'Application Accesses Content Via Unencrypted Channel'
    FINDINGS    = 'The Team found the application accessed the following content over unenecrypted communications:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        remove_urls = []
        urls = Utils.grep(r'http://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?', self.ANALYSIS.LOCAL_SMALI + "*")
        if urls:
            for f in urls:
                for finding in urls[f]:
                    if any(ignore in finding['code'] for ignore in IGNORE):
                        urls[f].remove(finding)

                if not urls[f]:
                    remove_urls += [f]

        for f in remove_urls:
            urls.pop(f)

        if urls:
            self.REPORT  = True
            self.DETAILS = Utils.grep_details(urls, self.ANALYSIS.LOCAL_SMALI)

