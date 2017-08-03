from os import path, walk
from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Shared Preferences Encryption Not Enforced Check'
    DESCRIPTION = 'Pulls the data cotnante and checks for any files on the shared_prefs folder'

    ID          = 'shared-pref-not-encrypted'
    ISSUE_TITLE = 'Application Does Not Enforce Shared Preferences Encryption'
    FINDINGS    = 'The Team found the following files in the \'shared_prefs\' folder were not encrypted:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        self.ANALYSIS.UTILS.launch_app()

        # pull data contents
        self.ANALYSIS.UTILS.pull_data_content(self.ANALYSIS.PACKAGE, self.ANALYSIS.LOCAL_DATA_CONTENT)
        shared_preferences = '{data}/{package}/shared_prefs'.format(data=self.ANALYSIS.LOCAL_DATA_CONTENT, package=self.ANALYSIS.PACKAGE)

        rfiles = []
        if path.exists(shared_preferences):
            for root, dirs, files in walk(shared_preferences, topdown=False):
                for name in files:
                    rfiles.append('/data/data/{package}/shared_prefs/{file}'.format(package=self.ANALYSIS.PACKAGE, file=name))

        if rfiles:
            self.DETAILS = '* {details}'.format(details='\n* '.join([f for f in rfiles]))
            self.REPORT  = True

