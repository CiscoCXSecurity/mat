from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Browsable Activities Check'
    DESCRIPTION = 'Checks if the application has activities that can be accessable from the browser'

    ID          = 'browsable'
    ISSUE_TITLE = 'Application Has Browsable Activities'
    FINDINGS    = 'The Team found the following browsable classes and URIs:\n'


    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        browsable_classes, browsable_uris = self.ANALYSIS.MANIFEST.browsable()
        if browsable_classes or browsable_uris:
            self.REPORT = True
            self.DETAILS =  '* URIs:\n * {details}'.format(details='\n * '.join(browsable_uris))
            self.DETAILS += '\n\n* Classes:\n * {details}'.format(details='\n * '.join(browsable_classes))

