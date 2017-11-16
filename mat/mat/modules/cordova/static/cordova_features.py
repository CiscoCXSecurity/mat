from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Insecure Cordova Features Check'
    DESCRIPTION = 'Checks if the cordova framework uses insecure features'

    ID          = 'insecure-features'
    ISSUE_TITLE = 'Application Uses Potential Insecure Cordova Features'
    FINDINGS    = 'The Team found that the Cordova framework contained potential insecure features:\n'

    def dependencies(self):
        return True

    def run(self):
        features = []

        if self.ANALYSIS.CONFIG_FILE:
            with open(self.ANALYSIS.CONFIG_FILE, 'r') as f:
                config = f.read()

            save = None
            for line in config.split('\n'):
                if '</feature' in line:
                    features += [save + '\n' + line]
                    print "SAVED: " + line
                    save = None
                elif not save and '<feature name=' in line:
                    print "FOUND: " + line
                    save = line
                elif save:
                    print "ADDING: " + line
                    save += '\n' + line

        if features:
            self.REPORT = True
            self.DETAILS = '<code>\n{details}\n</code>'.format(details='\n'.join(features))
