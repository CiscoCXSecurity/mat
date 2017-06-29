from os import popen, getenv

rows, columns  = popen('stty size', 'r').read().split()
rows           = int(rows)
columns        = int(columns)

# files settings
output         = 'mat-output'

# boolean / test settings
static         = False
device         = False
avd            = None

SILENT         = False
DEBUG          = False

# android files shipped with the application
LOCAL_LIB      = '{home}/.config/audits/lib'.format(home=getenv('HOME'))
dex2jar        = '{lib}/dex2jar/d2j-dex2jar.sh'.format(lib=LOCAL_LIB)
apktool        = '{lib}/apktool'.format(lib=LOCAL_LIB)
jdcli          = '{lib}/jd-cli'.format(lib=LOCAL_LIB)

# ios files shipped with the application
dump_fileprot  = '{lib}/dump_fileprotection'.format(lib=LOCAL_LIB)
dump_log       = '{lib}/dump_log'.format(lib=LOCAL_LIB)
ssh_ios        = '{lib}/sshios'.format(lib=LOCAL_LIB)
scp_to_ios     = '{lib}/scptoios'.format(lib=LOCAL_LIB)
scp_from_ios   = '{lib}/scpfromios'.format(lib=LOCAL_LIB)
tcprelay       = '{lib}/tcprelay.py'.format(lib=LOCAL_LIB)
dump_decrypt   = '{lib}/dumpdecrypted.dylib'.format(lib=LOCAL_LIB)
class_dump     = '{lib}/class-dump'.format(lib=LOCAL_LIB)
class_dump_mac = '{lib}/class-dump-macos'.format(lib=LOCAL_LIB)
fsmon          = '{lib}/fsmon'.format(lib=LOCAL_LIB)
keychain_dump  = '{lib}/keychain_dump'.format(lib=LOCAL_LIB)

# signing  dependencies
signjar        = '{lib}/signing/signapk.jar'.format(lib=LOCAL_LIB)
cert           = '{lib}/signing/cert.x509.pem'.format(lib=LOCAL_LIB)
pk8            = '{lib}/signing/key.pk8'.format(lib=LOCAL_LIB)

# android apps
drozer_agent   = '{lib}/drozer-agent.apk'.format(lib=LOCAL_LIB)
proxy_setter   = '{lib}/proxy-setter.apk'.format(lib=LOCAL_LIB)
busybox_bins   = '{lib}/bb-bins.zip'.format(lib=LOCAL_LIB)

# static analysis settings
minsdk         = '21'
targetsdk      = '25'
maxsdk         = '25'
apkfilename    = None

# ios settings
app            = None
APPS_PATH_9    = '/var/containers/Bundle/Application/'
APPS_PATH_8    = '/var/mobile/Containers/Bundle/Application'
APPS_PATH_7    = '/var/mobile/Applications'

# save the issues found:
results        = []

################################################################################
#    ANDROID
################################################################################

# excessive permissions
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

# Android Issues
ANDROID_ISSUES = {
    ####################################
    # STATIC
    ####################################

    'webviewredirect': {
        'title': 'Application `WebView\' Component Permits Arbitrary URL Redirection',
        'issue-id': 'webview-redirect',
        'regex': [
            {'regex': r'import android\.webkit\.WebView'},
            {'regex': r'shouldOverrideUrlLoading\(', 'report-if-not-found': True}
        ],
        'type': 'static'
    },

    'webviewcache': {
        'title': 'Application Does Not Delete WebView Cache Files On Exit',
        'issue-id': 'webview-cache',
        'regex': [
            {'regex': r'import android\.webkit\.WebView'},
            {'regex': r'clearCache\(', 'report-if-not-found': True}
        ],
        'type': 'static'
    },

    'webviewfiles': {
        'title': 'Application Does Not Disable File Access On `WebView\' Component',
        'issue-id': 'webview-files',
        'regex': [
            {'regex': r'import android\.webkit\.WebView'},
            {'regex': r'setAllowFileAccess\(false\)', 'report-if-not-found': True}
        ],
        'type': 'static'
    },

    'fragment': {
        'title': 'Application Vulnerable To Fragment Injection',
        'issue-id': 'fragment-injection',
        'regex': [
            {'regex': r'extends PreferenceActivity', 'report-if-found': True},
        ],
        'min_secure_sdk': True,
        'type': 'static'
    },

    'javascript': {
        'title': 'Application Enables JavaScript On `WebView\' Component',
        'issue-id': 'javascript-enabled',
        'regex': [
            {'regex': r'import android\.webkit\.WebView'},
            {'regex': r'setJavaScriptEnabled\(true\)', 'report-if-found': True},
        ],
        'type': 'static'
    },

    'bridge': {
        'title': 'Application Utilises JavaScript Bridge Between `WebView\' And Native Code',
        'issue-id': 'javascript-bridge',
        'regex': [
            {'regex': r'import android\.webkit\.WebView'},
            {'regex': r'addJavascriptInterface\(', 'report-if-found': True},
            {'regex': r'loadUrl\('},
            {'regex': r'@JavascriptInterface', 'report-if-found': True},
        ],
        'type': 'static'
    },

    'logcat': {
        'title': 'Application Logs To LogCat',
        'issue-id': 'logcat',
        'regex': [
            {'regex': r'Log\.(w|i|v|e)\(', 'report-if-found': False},
        ],
        'type': 'static'
    },

    'unencrypted': {
        'title': 'Application Downloads Content Via Unencrypted Channel',
        'issue-id': 'unencrypted-download',
        'regex': [
            {'regex': r'http://', 'report-if-found': False},
        ],
        'type': 'static'
    },

    ####################################
    # MANIFEST | STATIC
    ####################################

    'permissions': {
        'title': 'Application Uses Inadequate Permissions',
        'issue-id': 'inadequate-permissions',
        'finding': 'The following permissions where identified in the android manifest:\n',
        'type': ['manifest', 'static']
    },

    'debuggable': {
        'title': 'Application Identified As Debuggable',
        'issue-id': 'debuggable',
        'type': ['manifest', 'static']
    },

    'backup': {
        'title': 'Mobile Application Permits Backups',
        'issue-id': 'permits-backups',
        'type': ['manifest', 'static']
    },

    'minsdk': {
        'title': 'Out-Of-Date Android SDK Supported',
        'issue-id': 'out-of-date-sdk',
        'type': ['manifest', 'static']
    },

    'targetsdk': {
        'title': 'Application Does Not Target The Latest Android API Level',
        'issue-id': 'latest-api',
        'type': ['manifest', 'static']
    },

    ####################################
    # DYNAMIC
    ####################################

    'emulator': {
        'title': 'Inadequate Detection Of Emulator Devices',
        'issue-id': 'emulator',
        'finding': 'The Team identified that the application did not perform emulator detection.\n[TODO]Check Manually[/TODO]',
        'type': 'dynamic'
    },

    'pathtraversal': {
        'title': 'Application Has Provider Vulnerable To Directory Traversal',
        'issue-id': 'dir-traversal',
        'finding': 'The Team found the following providers to be vulnerable to path traversal:\n',
        'type': 'dynamic'
    },

    'injection': {
        'title': 'Application Has Provider Vulnerable To SQL Injection',
        'issue-id': 'sql-injection',
        'finding': 'The Team identified the following providers to be vulnerable to SQL injection:\n',
        'type': 'dynamic'
    },

    'secretcodes': {
        'title': 'Application Has Secret Codes',
        'issue-id': 'secret-codes',
        'finding': 'The Team found the following secret codes associated with application:\n',
        'type': 'dynamic'
    },

    'worldreadable': {
        'title': 'Application Data Has World Readable Files',
        'issue-id': 'world-readable',
        'finding': 'The Team found the following world readable files in the application\'s data:\n',
        'type': 'dynamic'
    },

    'worldwritable': {
        'title': 'Application Data Has World Writable Files',
        'issue-id': 'world-writable',
        'finding': 'The Team found the following world writable files in the application\'s data:\n',
        'type': 'dynamic'
    },

    'sharedpref': {
        'title': 'Shared Preferences Encryption Not Enforced',
        'issue-id': 'shared-pref-not-encrypted',
        'finding': 'The Team found the following files in the `shared_prefs\' folder were not encrypted:\n\n[TODO]Check Manually[/TODO]',
        'type': 'dynamic'
    },

    'root': {
        'title': 'Application Does Not Perform Root Detection',
        'issue-id': 'root-detection',
        'finding': 'The Team identified that the application did not perform root detection.\n[TODO]Check Manually[/TODO]',
        'type': 'dynamic'
    }
}

# unused
DATA_KEYWORD_CHECKS = ['password', 'user', 'salt', 'code', 'pin', 'key', 'token']

################################################################################
#    GENERAL
################################################################################

IGNORE = [
    {'pattern': '/com/google/', 'path': True},
    {'pattern': '/android/', 'path': True},
    {'pattern': '/Frameworks/', 'path': True}
]

################################################################################
#    IOS
################################################################################

IOS_IGNORED_FILE_EXT = ['png', 'nib', 'jpg', 'gif', 'ttf']

IOS_PERMISSIONS = [
    'NSAppleMusicUsageDescription', 'NSBluetooth', 'NSCalendarsUsage',
    'NSCameraUsage', 'NSContactsUsage', 'NSHealthShareUsage',
    'NSHealthUpdateUsage', 'NSHomeKitUsage', 'NSLocation', 'NSMicrophone',
    'NSMotionUsage', 'NSPhotoLibraryUsage', 'NSRemindersUsage', 'NSLocationAlwaysUsageDescription'
]

IOS_ISSUES = {
    'unencrypted-download' : {
        'title': 'Application Downloads Content Via Unencrypted Channel',
        'issue-id': 'unencrypted-download',
        'regex': 'http://',
        'ignore-case': False,
        'reverse': False,
        'strings': True,
        'include-findings': True
    },

    'insecure-ats': {
        'title': 'Application Has Insecure Application Transport Security Settings',
        'issue-id': 'insecure-ats',
        'include-findings': True
    },

    'excessive-permissions': {
        'title': 'Application Implements Excessive Permissions',
        'issue-id': 'excessive-permissions',
        'include-findings': True
    },

    'keychain-data': {
        'title': 'Data Stored In Keychain Unencrypted',
        'issue-id': 'keychain-data',
        'include-findings': True
    },

    'arc-support': {
        'regex': '_objc_init|_objc_load|_objc_store|_objc_move|_objc_copy|_objc_retain|_objc_unretain|_objc_release|_objc_autorelease',
        'ignore-case': False,
        'reverse': True,
        'title': 'Application does not use ARC APIs',
        'issue-id': 'arc-support',
        'include-findings': False
    },

    'root-detected': {
        'title': 'Application Performs Jailbreak Detection [CHECK MANUALLY]',
        'issue-id': 'root-detection',
        'include-findings': True
    },

    'root-detection': {
        'regex': 'jailbreak|cydia',
        'ignore-case': True,
        'reverse': True,
        'title': 'Application Does Not Perform Jailbreak Detection',
        'issue-id': 'root-detection',
        'include-findings': False,
    },

    'ssl-pinning': {
        'regex': 'setAllowInvalidCertificates|allowsInvalidSSLCertificate|validatesDomainName|SSLPinningMode',
        'ignore-case': False,
        'reverse': False,
        'title': 'SSL Certificate Pinning Not In Use',
        'issue-id': 'ssl-pinning',
        'include-findings': False
    },

    'sys-log': {
        'regex': 'NSLog',
        'ignore-case': False,
        'reverse': False,
        'title': 'Application Logs To Console Log',
        'issue-id': 'sys-log',
        'strings': True,
        'include-findings': True
    },

    'weak-crypto': {
        'regex': 'kCCAlgorithmDES|kCCAlgorithm3DES|kCCAlgorithmRC2|kCCAlgorithmRC4|kCCOptionECBMode|kCCOptionCBCMode|DES|3ES|RC2|RC4|ECB|CBC',
        'ignore-case': False,
        'reverse': False,
        'title': 'Weak Encryption and Hashing Algorithms',
        'issue-id': 'weak-crypto',
        'include-findings': False
    },

    'banned-apis': {
        'regex': 'malloc|alloca|gets|memcpy|scanf|sprintf|sscanf|strcat|StrCat|strcpy|StrCpy|strlen|StrLen|strncat|StrNCat|strncpy|StrNCpy|strtok|swprintf|vsnprintf|vsprintf|vswprintf|wcscat|wcscpy|wcslen|wcsncat|wcsncpy|wcstok|wmemcpy',
        'ignore-case': False,
        'reverse': False,
        'title': 'Binary Application Utilises Unsafe "Banned" Library Functions [USE WITH CAUTION - DOUBLE CHECK]',
        'issue-id': 'banned-apis',
        'include-findings': False
    },

    'weak-random': {
        'regex': 'srand|random',
        'ignore-case': False,
        'reverse': False,
        'title': 'Application Generates Insecure Random Numbers [USE WITH CAUTION - DOUBLE CHECK]',
        'issue-id': 'weak-random',
        'include-findings': False
    },

    'debugger-detection': {
        'regex': 'ptrace',
        'ignore-case': True,
        'reverse': True,
        'title': 'Debugger Detection Not Present',
        'issue-id': 'debugger-detection',
        'include-findings': False
    },

    'insecure-channel': {
        'regex': 'SSLSetEnabledCiphers|TLSMinimumSupportedProtocol|TLSMaximumSupportedProtocol',
        'ignore-case': False,
        'reverse': True,
        'title': 'Binary Application Communicates Over Insecure Channel',
        'issue-id': 'insecure-channel',
        'include-findings': True
    },

    'pie-support': {
        'title': 'Application Not Compiled With PIE',
        'issue-id': 'pie-support',
        'include-findings': False
    },

    'file-protection': {
        'title': 'Application Does Not Use Complete File Protection',
        'issue-id': 'file-protection',
        'include-findings': True
    },
}

CORDOVA_ISSUES = {

    'outdated': {
        'title': 'Out-Of-Date Cordova Framework In Use',
        'issue-id': 'out-of-date',
        'include-findings': True
    },

    'todo': {
        'title': 'Incomplete Code',
        'issue-id': 'incomplete-code',
        'include-findings': True
    },

    'open': {
        'title': 'Cordova Extensions Have Open Origin',
        'issue-id': 'open-origin',
        'include-findings': True
    },
}