from mat.utils.utils import Issue

IOS_PERMISSIONS = [
    'NSAppleMusicUsageDescription', 'NSBluetooth', 'NSCalendarsUsage',
    'NSCameraUsage', 'NSContactsUsage', 'NSHealthShareUsage',
    'NSHealthUpdateUsage', 'NSHomeKitUsage', 'NSLocation', 'NSMicrophone',
    'NSMotionUsage', 'NSPhotoLibraryUsage', 'NSRemindersUsage', 'NSLocationAlwaysUsageDescription'
]

class Issue(Issue):

    TITLE       = 'Excessive Permissions Check'
    DESCRIPTION = 'Runs several tests to determine if the application uses excessive permissions'

    ID          = 'excessive-permissions'
    ISSUE_TITLE = 'Application Implements Excessive Permissions'
    FINDINGS    = 'The Team identified the following excessive permissions used by the application:\n'

    def run(self):
        entitlements = self.ANALYSIS.UTILS.get_entitlements(self.ANALYSIS.IOS_BIN_PATH)

        permissions = []
        if 'get-tasks-allow' in entitlements and entitlements['get-tasks-allow']:
            permissions += ['get-tasks-allow']

        for permission in IOS_PERMISSIONS:
            if permission in self.ANALYSIS.APP_INFO and self.ANALYSIS.APP_INFO[permission]:
                permissions += [permission]

        if permissions:
            self.DETAILS = '* {details}'.format(details='* '.join(permissions))
            self.REPORT  = True


