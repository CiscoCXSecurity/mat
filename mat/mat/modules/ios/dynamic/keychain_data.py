from mat.utils.utils import Issue

class Issue(Issue):

    TITLE       = 'Keychain Data Check'
    DESCRIPTION = 'Dumps keychain data and looks for data related to the application'

    ID          = 'keychain-data'
    ISSUE_TITLE = 'Application Stores Unencrypted Data In Keychain'
    FINDINGS    = 'The following data was found in the keychain:\n'

    def run(self):
        entitlements = self.ANALYSIS.UTILS.get_entitlements(self.ANALYSIS.IOS_BIN_PATH)

        # keychain dump
        # keys.plist, cert.plist, inet.plist, genp.plist -> ID: agrp, DATA: data
        if 'keychain-access-groups' in entitlements:

            self.ANALYSIS.UTILS.dump_keychain(self.ANALYSIS.IOS_WORKING_FOLDER)

            keys = self.ANALYSIS.UTILS.get_plist('{working}/keys.plist'.format(working=self.ANALYSIS.IOS_WORKING_FOLDER))
            keys += self.ANALYSIS.UTILS.get_plist('{working}/genp.plist'.format(working=self.ANALYSIS.IOS_WORKING_FOLDER))
            keys += self.ANALYSIS.UTILS.get_plist('{working}/cert.plist'.format(working=self.ANALYSIS.IOS_WORKING_FOLDER))
            keys += self.ANALYSIS.UTILS.get_plist('{working}/inet.plist'.format(working=self.ANALYSIS.IOS_WORKING_FOLDER))

            keychainids = entitlements['keychain-access-groups']

            data =[]
            for key in keys:
                if key['agrp'] in keychainids:
                    data += [str(key['data']) if 'data' in key else str(key)]

            if data:
                self.DETAILS = '<code>{data}</code>'.format(data='</code><code>'.join(data))
                self.REPORT  = True
