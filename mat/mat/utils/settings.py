from os import getenv

LOCAL_SETTINGS  = "{home}/.mat".format(home=getenv('HOME'))

# files settings
output          = 'mat-output'

# boolean / test settings
static          = False
device          = False
avd             = "MAT-Testing"

SILENT          = False
DEBUG           = False

# binaries
find            = None
file            = None
grep            = None
egrep           = None
java            = None
drozer          = None
unzip           = None
strings         = None
md5sum          = None
adb             = None
emulator        = None
sdkmanager      = None
avdmanager      = None
expect          = None
plutil          = None

# android files shipped with the application
LOCAL_LIB       = '{local}/lib'.format(local=LOCAL_SETTINGS)
dex2jar         = '{lib}/dex2jar/d2j-dex2jar.sh'.format(lib=LOCAL_LIB)
apktool         = '{lib}/apktool'.format(lib=LOCAL_LIB)
jdcli           = '{lib}/jd-cli'.format(lib=LOCAL_LIB)

# ios files shipped with the application
dump_fileprot   = '{lib}/dump_fileprotection'.format(lib=LOCAL_LIB)
dump_log        = '{lib}/dump_log'.format(lib=LOCAL_LIB)
ssh_ios         = '{lib}/sshios'.format(lib=LOCAL_LIB)
scp_to_ios      = '{lib}/scptoios'.format(lib=LOCAL_LIB)
scp_from_ios    = '{lib}/scpfromios'.format(lib=LOCAL_LIB)
tcprelay        = '{lib}/tcprelay.py'.format(lib=LOCAL_LIB)
dump_decrypt    = '{lib}/dumpdecrypted.dylib'.format(lib=LOCAL_LIB)
class_dump      = '{lib}/class-dump'.format(lib=LOCAL_LIB)
class_dump_mac  = '{lib}/class-dump-macos'.format(lib=LOCAL_LIB)
fsmon           = '{lib}/fsmon'.format(lib=LOCAL_LIB)
keychain_dump   = '{lib}/keychain_dump'.format(lib=LOCAL_LIB)
backup_excluded = '{lib}/backup_excluded'.format(lib=LOCAL_LIB)

# signing  dependencies
signjar         = '{lib}/signing/signapk.jar'.format(lib=LOCAL_LIB)
cert            = '{lib}/signing/cert.x509.pem'.format(lib=LOCAL_LIB)
pk8             = '{lib}/signing/key.pk8'.format(lib=LOCAL_LIB)

# android apps
drozer_agent    = '{lib}/drozer-agent.apk'.format(lib=LOCAL_LIB)
proxy_setter    = '{lib}/proxy-setter.apk'.format(lib=LOCAL_LIB)
busybox_bins    = '{lib}/bb-bins.zip'.format(lib=LOCAL_LIB)

# static analysis settings
apkfilename     = None

# ios settings
app             = None

# save the issues found:
results         = []

# cli defaults
type        = "android"
runchecks   = False
uninstall   = False
clean       = False
listapps    = False
ipa         = None
install     = False
update      = False
modify      = False
proxy       = None
unproxy     = False
apk         = None
package     = None
compile     = False

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

IGNORED_FILE_EXT = ['png', 'nib', 'jpg', 'gif', 'ttf']