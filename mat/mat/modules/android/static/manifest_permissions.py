from mat.utils.utils import Issue

ANDROID_PERMISSIONS = [
    'android.permission.GET_TASKS', 'android.permission.BIND_DEVICE_ADMIN',
    'android.permission.USE_CREDENTIALS', 'com.android.browser.permission.READ_HISTORY_BOOKMARKS',
    'android.permission.PROCESS_OUTGOING_CALLS', 'android.permission.READ_LOGS',
    'android.permission.READ_SMS', 'android.permission.READ_CALL_LOG',
    'android.permission.RECORD_AUDIO', 'android.permission.MANAGE_ACCOUNTS',
    'android.permission.RECEIVE_SMS', 'android.permission.RECEIVE_MMS',
    'android.permission.WRITE_CONTACTS', 'android.permission.DISABLE_KEYGUARD',
    'android.permission.WRITE_SETTINGS', 'android.permission.WRITE_SOCIAL_STREAM',
    'android.permission.BIND_DEVICE_ADMIN', 'android.permission.WAKE_LOCK'
]

class Issue(Issue):

    TITLE       = 'Inadequate Permissions Check'
    DESCRIPTION = 'Searches the Manifest file for inadequace permissions'

    ID          = 'inadequate-permissions'
    ISSUE_TITLE = 'Application Uses Inadequate Permissions'
    FINDINGS    = 'The following permissions where identified in the android manifest:\n'

    def dependencies(self):
        return self.ANALYSIS.UTILS.check_dependencies(['static'])

    def run(self):
        permissions = []
        for permission in self.ANALYSIS.MANIFEST.permissions():
            if permission in ANDROID_PERMISSIONS:
                permissions.append(permission)

        if permissions:
            self.DETAILS = '* {details}'.format(details='\n* '.join(permissions))
            self.REPORT  = True



