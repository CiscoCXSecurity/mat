from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'World Writable Data Files Check'
    DESCRIPTION = 'Checks for world writable data files'

    ID          = 'world-writable'
    ISSUE_TITLE = 'Application Data Has World Writable Files'
    FINDINGS    = 'The Team found the following world writable files in the application\'s data:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        world_writable_files = self.ANALYSIS.UTILS.find_world_files(self.ANALYSIS.REMOTE_DATA_FOLDER, 'w')
        if world_writable_files:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(world_writable_files.split('\n')))

