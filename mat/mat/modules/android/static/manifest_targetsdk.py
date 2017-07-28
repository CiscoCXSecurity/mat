from utils.utils import Issue

ANDROID_TARGET_SDK = '26'

class Issue(Issue):

    TITLE       = 'Target SDK Check'
    DESCRIPTION = 'Searches the manifest / apktool yaml file for target sdk tag'

    ID          = 'latest-api'
    ISSUE_TITLE = 'Application Does Not Target The Latest Android API Level'
    FINDINGS    = 'The application was found to target the following SDKs:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        if self.ANALYSIS.MANIFEST.get_sdk('target') < ANDROID_TARGET_SDK:
            self.DETAILS = '* Current target SDK version\n<code>\ntargetSdkVersion="{targetsdk}"\n</code>'.format(targetsdk=self.ANALYSIS.MANIFEST.get_sdk('target'))
            self.REPORT  = True

