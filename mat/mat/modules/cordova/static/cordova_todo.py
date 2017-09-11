from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Imcomplete Code Cordova Check'
    DESCRIPTION = 'Checks if the cordova framework contains imcomplete code'

    ID          = 'incomplete-code'
    ISSUE_TITLE = 'Application Cordova Framework Contains Incomplete Code'
    FINDINGS    = 'The Team found that the Cordova framework contained incomplete code:\n'

    def dependencies(self):
        return True

    def run(self):
        todo = []

        if self.ANALYSIS.CORDOVA_FILE:
            with open(self.ANALYSIS.CORDOVA_FILE, 'r') as f:
                cordova = f.read()

            for line in cordova.split('\n'):
                if 'TODO:' in line:
                    todo += [line.strip()]

        if todo:
            self.DETAILS = '<code>{todo}</code>'.format(todo='\n'.join(todo))
            self.REPORT  = True

