import re

from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'SSL Pinning Check'
    DESCRIPTION = 'Checks if SSL Pinning is not implemented'

    ID          = 'ssl-pinning'
    ISSUE_TITLE = 'Application Does Not Implemented SSL Pinning'
    FINDINGS    = 'The Team found the application did not implement SSL Pinning'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):

        files = Utils.grep(r'X509TrustManager|getAcceptedIssuers|checkClientTrusted|checkServerTrusted', self.ANALYSIS.LOCAL_SMALI + '*')

        if not files:
            self.REPORT = True
            self.FINDINGS = 'No evidence of TrustManager being used was found.'

        self.DETAILS = ''
        for f in files:
            with open(f, 'r') as d:
                smali = d.read()

            if re.search(r'.method.*checkServerTrusted(.*\n)*?[ \t]*\.prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*return-void', smali):
                self.REPORT = True
                self.DETAILS += '\n* {file}:\n\n<code>{method}</code>\n'.format(file=f.replace(self.ANALYSIS.LOCAL_SMALI, 'smali'), method=self.ANALYSIS.UTILS.get_smali_method('checkServerTrusted', f))

            if re.search(r'.method.*getAcceptedIssuers(.*\n)*?[ \t]*\.prologue\n(([\t ]*(\.line.*)?)\n)*[ \t]*const\/4 v0, 0x0\n[ \n\t]*return-object v0', smali):
                self.REPORT = True
                self.DETAILS += '\n* {file}:\n\n<code>{method}</code>\n'.format(file=f.replace(self.ANALYSIS.LOCAL_SMALI, 'smali'), method=self.ANALYSIS.UTILS.get_smali_method('getAcceptedIssuers', f))

