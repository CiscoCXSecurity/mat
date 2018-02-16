from mat.utils.utils import Utils, Issue

ANDROID_STATIC_RESPONSES = [
    'android.test.purchased',
    'android.test.canceled',
    'android.test.item_unavailable',
    'android.test.refunded'
]

class Issue(Issue):

    TITLE       = 'InApp Billing Static Responses Check'
    DESCRIPTION = 'Checks if the application uses Static Responses for the InApp Billing'

    ID          = 'inapp-billing-static-responses'
    ISSUE_TITLE = 'Application Uses InAPP Billing Static Responses'
    FINDINGS    = 'The Team found the InApp Billing implementation uses the following static reponses:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):

        for response in ANDROID_STATIC_RESPONSES:
            files = Utils.grep(r'' + response + '', self.ANALYSIS.LOCAL_SOURCE)
            if files:
                self.REPORT  = True
                self.DETAILS = '* {static}'.format(static=response+'\n')
                self.DETAILS += Utils.grep_details(files, self.ANALYSIS.LOCAL_SOURCE)
