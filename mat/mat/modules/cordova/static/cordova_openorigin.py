from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Open Origin Cordova Extensions Check'
    DESCRIPTION = 'Checks if the cordova framework contains open origin extensions'

    ID          = 'open-origin'
    ISSUE_TITLE = 'Application Cordova Extensions Have Open Origin'
    FINDINGS    = 'The Team found that the Cordova framework in use contained open origin extensions:\n'

    def dependencies(self):
        return True

    def run(self):
        open_origin = None
        if self.ANALYSIS.CONFIG_FILE:
            with open(self.ANALYSIS.CONFIG_FILE, 'r') as f:
                config = f.read()

            for line in config.split('\n'):
                if '<access origin="*"' in line:
                    open_origin = line.strip()

        if open_origin:
            self.DETAILS = '<code>{open}</code>'.format(open=open_origin)
            self.REPORT  = True

