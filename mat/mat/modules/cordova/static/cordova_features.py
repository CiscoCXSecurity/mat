from utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Insecure Cordova Features Check'
    DESCRIPTION = 'Checks if the cordova framework uses insecure features'

    ID          = 'insecure-features'
    ISSUE_TITLE = 'Application Uses Insecure Cordova Features'
    FINDINGS    = 'The Team found that the Cordova framework used contained insecure features:\n'

    def dependencies(self):
        return True

    def run(self):
        features = []

        if self.ANALYSIS.CONFIG_FILE:
            with open(self.ANALYSIS.CONFIG_FILE, 'r') as f:
                config = f.read()

            for line in config.split('\n'):
                if '<feature name=' in line:
                    features += [line.strip()]

        if features:
            # TODO: not reporting self.FEATURES just yet - need to check which are actually dangerous
            pass

