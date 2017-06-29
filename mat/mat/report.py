from json import dumps
import settings

# Log
from utils import Log

class Report():

    FILENAME = 'issues'

    @staticmethod
    def reportToXML():
        Report.FILENAME = settings.apk if settings.apk else (settings.app[0].split('/')[1] if settings.app else 'issues')
        with open('{output}/{name}.{type}.xml'.format(output=settings.output, name=Report.FILENAME, type=settings.type), 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?><issues>\n')
            for issue in settings.results:
                line = '\t<issue id={id}>\n\t\t<title>{title}</title>\n\t\t<findings>{findings}</findings>\n\t\t<details>{details}</details>\n\t</issue>\n'
                details = '\n* '.join(issue.finding_details) if isinstance(issue.finding_details, list) else issue.finding_details
                f.write(line.format(id=issue.issue_id, title=issue.title, findings=issue.findings, details=details))
            f.write('</issues>')

    @staticmethod
    def reportToJson(alias=None):
        if 'android' in settings.type:
            Report.FILENAME = (settings.apk.rsplit('/', 1)[1] if '/' in settings.apk else settings.apk) if settings.apk else (settings.package if settings.package else 'mobile.app')

        if 'ios' in settings.type:
            Report.FILENAME = settings.app if settings.app else 'mobile.app'

        alias = '{type} {name}'.format(type='iOS' if 'ios' in settings.type else 'Android', name=Report.FILENAME if not alias else alias)

        with open('{output}/{name}.{type}.json'.format(output=settings.output, name=Report.FILENAME, type=settings.type), 'w') as f:
            rdict = {'app-name': alias, 'issues': [{'id': issue.issue_id, 'title': issue.title, 'findings': issue.findings, 'details': issue.finding_details} for issue in settings.results]}
            f.write(dumps(rdict))

    @staticmethod
    def reportToTerminal():
        print('\nThe following issues were found:')
        for issue in settings.results:
            #print('{id} - {title}'.format(id=issue.issue_id, title=issue.title))
            print('* {title}'.format(title=issue.title))
        print('')

class Issue():

    def __init__(self, title, issue_id, findings, finding_details=None):
        self.title = title
        self.issue_id = issue_id
        self.findings = findings or ''
        self.finding_details = finding_details or ''

        Log.d('\n'+self.print_issue(False))

    @staticmethod
    def load(issue=None):
        if not issue: return None
        return Issue(issue['title'], issue['id'], issue['findings'], issue['details'])

    def print_issue(self, tprint=True):
        result =  '---------------------------------- ISSUE ----------------------------------\n'
        result += 'TITLE:\n{title}\n'.format(title=self.title)
        result += 'FINDINGS:\n{findings}\n'.format(findings=self.findings)
        result += 'FINDING DETAILS:\n{details}\n'.format(details=self.finding_details)
        result += '----------------------------------  END  ----------------------------------\n'

        if tprint:
            print(result)

        return result
