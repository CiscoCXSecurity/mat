from os import makedirs as _makedirs
from os.path import exists as _exists

from json import dumps, loads

# Log
from utils import Log

class Report():

    def __init__(self, output_path, alias, assessment_type):
        self.OUTPUT_PATH    = output_path
        self.ALIAS          = alias
        self.ASESSMENT_TYPE = assessment_type

    def report_to_json(self, results):

        filename = self.ALIAS.replace(' ', '.').lower()
        alias = '{type} {name}'.format(type=self.ASESSMENT_TYPE, name=self.ALIAS)

        # create output dir if it doesn't exist
        if not _exists(self.OUTPUT_PATH):
            _makedirs(self.OUTPUT_PATH)

        with open('{output}/{name}.{type}.json'.format(output=self.OUTPUT_PATH, name=filename, type=self.ASESSMENT_TYPE.lower()), 'w') as f:
            rdict = {
                'app-name': alias,
                'type': self.ASESSMENT_TYPE,
                'issues': [
                    {
                        'id': issue.ID,
                        'title': issue.ISSUE_TITLE,
                        'findings': issue.FINDINGS,
                        'details': issue.DETAILS
                    } for issue in results
                ]}
            f.write(dumps(rdict))

    def report_to_terminal(self, results):
        print('\nThe following issues were found:')
        for issue in results:
            print('* {title}'.format(title=issue.ISSUE_TITLE))
        print('')

    @staticmethod
    def print_report(location):
        with open(location, 'r') as f:
            report = loads(f.read())
        for i in report['issues']:
            issue = ReportIssue.load(i)
            print issue.issue()

        result = '{top}\n{space}{title}\n{top}\n'.format(top='*'*80, space=' '*((80 - len(report['app-name']))/2), title=report['app-name'])

class ReportIssue():

    def __init__(self, title, issue_id, findings, finding_details=None):
        self.ISSUE_TITLE = title
        self.ID = issue_id
        self.FINDINGS = findings or ''
        self.DETAILS = finding_details or ''

        Log.d('\n'+self.issue())

    def issue(self):
        """
        result =  '---------------------------------- ISSUE ----------------------------------\n'
        result += 'TITLE:\n{title}\n'.format(title=self.ISSUE_TITLE)
        result += 'FINDINGS:\n{findings}\n'.format(findings=self.FINDINGS)
        result += 'FINDING DETAILS:\n{details}\n'.format(details=self.DETAILS)
        result += '----------------------------------  END  ----------------------------------\n'
        """
        result = '{top}\n{space}{title}\n{top}\n'.format(top='*'*80, space=' '*((80 - len(self.ISSUE_TITLE))/2), title=self.ISSUE_TITLE)
        result += '{finding}\n{details}\n'.format(finding=self.FINDINGS, details=self.DETAILS)

        return result

    @staticmethod
    def load(issue):
        return ReportIssue(issue['title'], issue['id'], issue['findings'], issue['details'])

