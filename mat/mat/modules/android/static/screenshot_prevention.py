from utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'Screenshot Prevention Check'
    DESCRIPTION = 'Looks into the decompiled app for screenshot protection flags'

    ID          = 'screenshot-prevention'
    ISSUE_TITLE = 'Application Permits Sensitive Information To Be Stored In Screenshots'
    FINDINGS    = 'The Team identified that the application did not prevent Android from taking screenshots containing sensitive information on the running application on the following Activities:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        activities = Utils.grep(r'onCreate\(', self.ANALYSIS.LOCAL_SOURCE) or []
        safe_activities = Utils.grep(r'FLAG_SECURE', ' '.join(list(activities))) or []
        report_activities = list(set(activities) - set(safe_activities))

        if report_activities:
            self.DETAILS = '* {details}'.format(details='\n* '.join([a.replace(self.ANALYSIS.LOCAL_SOURCE, '') for a in report_activities]))
            self.REPORT  = True

