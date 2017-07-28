from json import dumps
import settings

# Log
from utils import Log

class Report():

    FILENAME = 'issues'

    @staticmethod
    def report_to_json(alias=None):
        if 'android' in settings.type:
            Report.FILENAME = (settings.apk.rsplit('/', 1)[1] if '/' in settings.apk else settings.apk) if settings.apk else (settings.package if settings.package else 'mobile.app')

        if 'ios' in settings.type:
            Report.FILENAME = settings.app if settings.app else 'mobile.app'

        alias = '{type} {name}'.format(type='iOS' if 'ios' in settings.type else 'Android', name=Report.FILENAME if not alias else alias)

        with open('{output}/{name}.{type}.json'.format(output=settings.output, name=Report.FILENAME, type=settings.type), 'w') as f:
            rdict = {'app-name': alias, 'issues': [{'id': issue.ID, 'title': issue.ISSUE_TITLE, 'findings': issue.FINDINGS, 'details': issue.DETAILS} for issue in settings.results]}
            f.write(dumps(rdict))

    @staticmethod
    def report_to_terminal():
        print('\nThe following issues were found:')
        for issue in settings.results:
            print('* {title}'.format(title=issue.ISSUE_TITLE))
        print('')

class ReportIssue():

    def __init__(self, title, issue_id, findings, finding_details=None):
        self.ISSUE_TITLE = title
        self.ID = issue_id
        self.FINDINGS = findings or ''
        self.DETAILS = finding_details or ''

        Log.d('\n'+self.print_issue(False))

    @staticmethod
    def load(issue=None):
        if not issue: return None
        return Issue(issue['title'], issue['id'], issue['findings'], issue['details'])

    def print_issue(self, tprint=True):
        result =  '---------------------------------- ISSUE ----------------------------------\n'
        result += 'TITLE:\n{title}\n'.format(title=self.ISSUE_TITLE)
        result += 'FINDINGS:\n{findings}\n'.format(findings=self.FINDINGS)
        result += 'FINDING DETAILS:\n{details}\n'.format(details=self.DETAILS)
        result += '----------------------------------  END  ----------------------------------\n'

        if tprint:
            print(result)

        return result
