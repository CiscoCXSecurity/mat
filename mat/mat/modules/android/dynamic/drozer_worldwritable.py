from utils.utils import Issue
from utils.android import Drozer

class Issue(Issue):

    TITLE       = 'Drozer World Writable Data Files Check'
    DESCRIPTION = 'Uses drozer to check for world writable data files'

    ID          = 'world-writable'
    ISSUE_TITLE = 'Application Data Has World Writable Files'
    FINDINGS    = 'The Team found the following world writable files in the application\'s data:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['dynamic', 'drozer'])

    def run(self):
        self.ANALYSIS.launch_app()
        self.DROZER = Drozer(adb=self.ANALYSIS.ADB)

        result = Drozer.parse_output('', self.DROZER.writable(self.ANALYSIS.PACKAGE))
        if result:
            self.DETAILS = result
            self.REPORT  = True

        self.DROZER.stop()


