from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Secret Codes Search Check'
    DESCRIPTION = 'Looks for secret codes in the application'

    ID          = 'secret-codes'
    ISSUE_TITLE = 'Application Has Secret Codes'
    FINDINGS    = 'The Team found the following secret codes associated with application:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        codes = self.ANALYSIS.MANIFEST.secret_codes()

        if codes:
            self.REPORT = True
            self.DETAILS = '* {details}'.format(details='\n* '.join(vulnerable_providers))
            self.DETAILS += '\n\nTest the codes using:\n<code>adb shell su -c "am broadcast -a android.provider.Telephony.SECRET_CODE -d android_secret_code://CODE</code>"'

            """
            TODO: launch secret code and check if it works
            adb shell "su -c 'am broadcast -a android.provider.Telephony.SECRET_CODE -d android_secret_code://4636'"
            """

