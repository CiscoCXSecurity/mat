from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'World Readable Data Files Check'
    DESCRIPTION = 'Checks for world readable data files'

    ID          = 'world-readable'
    ISSUE_TITLE = 'Application Data Has World Readable Files'
    FINDINGS    = 'The Team found the following world readable files in the application\'s data:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic'])

    def run(self):
        world_readable_files = self.ANALYSIS.UTILS.find_world_files(self.ANALYSIS.REMOTE_DATA_FOLDER, 'r')
        if world_readable_files:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(world_readable_files.split('\n')))


