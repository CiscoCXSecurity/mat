from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Native Libraries Check'
    DESCRIPTION = 'Checks for native libraries being used by the application'

    ID          = 'native-libs'
    ISSUE_TITLE = 'Application Uses Native Libraries'
    FINDINGS    = 'The Team found the following native libraries being used by the application:\n'

    LIBRARY_PATHS = ['lib/arm', 'lib/arm64']

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        libraries = []
        for lib in self.LIBRARY_PATHS:
            lib_path = '{path}/{lib}'.format(path=self.ANALYSIS.REMOTE_APP_FOLDER, lib=lib)
            libraries += ['{path}/{lib}'.format(path=lib_path, lib=l) for l in self.ANALYSIS.UTILS.run_on_device('ls {path}'.format(path=lib_path))[0].split('\n')]

        libraries = sorted(set(libraries))
        if libraries:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(libraries))

            """
            TODO: check if there are known problems with those libraries
            """

