from mat.utils.utils import Issue

ANDROID_MIN_SDK = '21'

class Issue(Issue):

    TITLE       = 'Out-Of-Date SDK Supported Check'
    DESCRIPTION = 'Searches the manifest / apktool yaml file for min sdk tag'

    ID          = 'out-of-date-sdk'
    ISSUE_TITLE = 'Application Supports Out-Of-Date Android SDKs'
    FINDINGS    = 'The application was found to run on the following SDKs:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        if self.ANALYSIS.MANIFEST.get_sdk('min') < ANDROID_MIN_SDK:
            self.DETAILS = '* Minimal supported SDK version\n<code>\nminSdkVersion="{minsdk}"\n</code>'.format(minsdk=self.ANALYSIS.MANIFEST.get_sdk('min'))
            self.REPORT  = True

