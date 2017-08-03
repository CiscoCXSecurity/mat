#!/usr/bin/python
# -*- coding: utf-8 -*-

# system modules
from json import loads
from sys import argv, exit, path, stdin
from os import getenv, makedirs
from os.path import exists
import argparse

#local modules
from utils import settings
from utils.utils import Utils, Log, die
from utils.android import AndroidUtils, ADB
from utils.ios import IOSUtils
from utils.report import Report, ReportIssue

# android imports
from analysis.android import AndroidAnalysis
from analysis.ios import IOSAnalysis

"""
TODO:
 - change cordova version id on xdb to out-of-date-cordova
 - check that the Cisco app results are the same as the old MAT results
"""

"""
TODO LIST
* Add interactive mode
* Finish Cordova features check
* Change drozer checks for manual checks (remove drozer dependency)
"""

VERSION = '3.1.0'

BANNER = '''

          _____           _             _ _ _
         |  __ \         | |           | | (_)
         | |__) |__  _ __| |_ ___ _   _| | |_ ___
         |  ___/ _ \| '__| __/ __| | | | | | / __|
         | |  | (_) | |  | || (__| |_| | | | \__ \\
         |_|   \___/|_|   \__\___|\__,_|_|_|_|___/  Security

                          Mobile Assessment Tool v{version}

  Copyright 2017 - Portcullis, https://www.portcullis-security.com

  Your local settings will be under {lsettings}/mat_settings.py.
    '''.format(version=VERSION, lsettings=settings.LOCAL_SETTINGS)

def find_executables():
    # system installed packages
    settings.find        = Utils.run('which find')[0].split('\n')[0]
    settings.file        = Utils.run('which file')[0].split('\n')[0]
    settings.grep        = Utils.run('which grep')[0].split('\n')[0]
    settings.egrep       = Utils.run('which egrep')[0].split('\n')[0]
    settings.java        = Utils.run('which java')[0].split('\n')[0]
    settings.drozer      = Utils.run('which drozer')[0].split('\n')[0]
    settings.unzip       = Utils.run('which unzip')[0].split('\n')[0]
    settings.strings     = Utils.run('which strings')[0].split('\n')[0]
    settings.md5sum      = Utils.run('which md5sum')[0].split('\n')[0]

    # Android SDK dependencies
    settings.adb         = Utils.run('which adb')[0].split('\n')[0]
    settings.emulator    = Utils.run('which emulator')[0].split('\n')[0]
    settings.sdkmanager  = Utils.run('which sdkmanager')[0].split('\n')[0]
    settings.avdmanager  = Utils.run('which avdmanager')[0].split('\n')[0]

    # ios expect shell
    settings.expect      = Utils.run('which expect')[0].split('\n')[0]

    # ios plutil for plist files
    settings.plutil      = Utils.run('which plutil')[0].split('\n')[0]

def merge_settings():
    path.append(settings.LOCAL_SETTINGS)
    try:
        import mat_settings

        # emulator settings
        settings.avd     = mat_settings.avd    if hasattr(mat_settings, 'avd')    else settings.avd

        # boolean / test settings
        settings.device  = mat_settings.device if hasattr(mat_settings, 'device') else settings.device
        settings.SILENT  = mat_settings.SILENT if hasattr(mat_settings, 'SILENT') else settings.SILENT
        settings.DEBUG   = mat_settings.DEBUG  if hasattr(mat_settings, 'DEBUG')  else settings.DEBUG

    except ImportError:
        Log.e('Local settings not imported.')

def clargs():
    import textwrap
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=BANNER, epilog=textwrap.dedent('''\
        Example of usage:
            mat -D ios -a com.apple.TestFlight
            mat android -a /tmp/app.apk -o /tmp/mat-output
            mat -J json_file android
        '''))
    subparsers = parser.add_subparsers(dest='type', description='Select the type of assessment')
    iosparser = subparsers.add_parser('ios')
    androidparser = subparsers.add_parser('android')
    parser.add_argument('-S', '--silent',              required=False, default=False, action='store_true',                     help='Does not ouput any information to the console aside from errors')
    parser.add_argument('-D', '--debug',               required=False, default=False, action='store_true',                     help='Verbose mode, displays debug information as well')
    parser.add_argument('-J', '--json-print',          required=False, metavar='file',                                         help='Prints the isses from the json file provided')

    # specify ios app
    iosparser.add_argument('-a', '--app',              required=False, metavar='id',                                           help='Installed APP id to be tested')
    iosparser.add_argument('-i', '--ipa',              required=False, metavar='/path/to/file.ipa',                            help='IPA file to install and analyse')
    iosparser.add_argument('-s', '--static-only',      required=False, default=False, action='store_true',                     help='Perform static analysis only')

    iosparser.add_argument('-I', '--install',          required=False, metavar='/path/to/file.ipa',                            help='IPA file to just install')
    iosparser.add_argument('-m', '--modify',           required=False, metavar=('binary', 'hex_find', 'hex_replace'), nargs=3, help='Finds and replaces the binary instructions on the provided binary')

    iosparser.add_argument('-n', '--no-install',       required=False, default=False, action='store_true',                     help='Uninstalls the app once the analysis is completed (only when `-i` is used).')
    iosparser.add_argument('-k', '--no-keep',          required=False, default=False, action='store_true',                     help='Deletes the local data (decrypted binary, pulled IPA, data files, classes, etc.) once the analysis is complete')

    iosparser.add_argument('-r', '--run-checks',       required=False, default=False, action='store_true',                     help='Performs dependency checks for iOS')
    iosparser.add_argument('-o', '--output',           required=False, metavar='/path/to/',                                    help='Folder to where the tool will report')

    # ease of use options
    iosparser.add_argument('-u', '--update-apps',      required=False, default=False, action='store_true',                     help='Update iOS applications list')
    iosparser.add_argument('-l', '--list-apps',        required=False, default=False, action='store_true',                     help='Lists the iOS applications installed that can be assessed')

    iosparser.add_argument('-p', '--set-proxy',        required=False, metavar='ip:port',                                      help='Sets up a proxy on iOS preferences')
    iosparser.add_argument('-P', '--unset-proxy',      required=False, default=False, action='store_true',                     help='Unsets the proxy on iOS preferences')

    # specify android apps
    androidparser.add_argument('-a', '--apk',          required=False, metavar='apk_file',                                     help='Specify the APK file to be analysed')
    androidparser.add_argument('-i', '--package',      required=False, metavar='com.package.app',                              help='Specify the PACKAGE to be analysed')

    androidparser.add_argument('-s', '--static-only',  required=False, default=False, action='store_true',                     help='Perform static analysis only')
    androidparser.add_argument('-d', '--device',       required=False, metavar='device',                                       help='Specify the device to install the apk')
    androidparser.add_argument('-e', '--avd',          required=False, metavar='avd',                                          help='Specify the AVD emulator image name')

    # REFACTORED
    androidparser.add_argument('-l', '--list-apps',    required=False, default=False, action='store_true',                     help='Lists the Android applications installed that can be assessed')
    androidparser.add_argument('-g', '--compile',      required=False, metavar='/path/to/decompiled/',                         help='Specify the decompiled app to compile and sign')

    androidparser.add_argument('-n', '--no-install',   required=False, default=False, action='store_true',                     help='Uninstalls the application after the dynamic analysis')
    androidparser.add_argument('-k', '--no-keep',      required=False, default=False, action='store_true',                     help='Deletes the decompiled APK and all data after static analysis')

    androidparser.add_argument('-r', '--run-checks',   required=False, default=False, action='store_true',                     help='Performs dependency checks for Android')
    androidparser.add_argument('-o', '--output',       required=False, metavar='/path/to/',                                    help='Folder to where the tool will report')

    return parser.parse_args()

def parse_arguments():
    args = clargs()

    # main args
    settings.SILENT      = args.silent or settings.SILENT
    settings.DEBUG       = args.debug or settings.DEBUG
    settings.jsonprint   = args.json_print

    # assessment type
    settings.type        = args.type

    # common output and dependencies
    settings.runchecks   = args.run_checks
    settings.output      = args.output or settings.output

    # common cleanup settings
    settings.uninstall   = args.no_install
    settings.clean       = args.no_keep

    # common args
    settings.listapps    = args.list_apps
    settings.static      = args.static_only

    # ios args
    if settings.type == 'ios':
        settings.app     = args.app
        settings.ipa     = args.ipa
        settings.install = args.install
        settings.update  = args.update_apps
        settings.modify  = args.modify
        settings.proxy   = args.set_proxy.split(':', 1) if args.set_proxy else None
        settings.unproxy = args.unset_proxy

    # android args
    if settings.type == 'android':
        settings.device  = args.device or settings.device
        settings.avd     = args.avd or settings.avd
        settings.apk     = args.apk
        settings.package = args.package
        settings.compile = args.compile

def run_ios():
    if settings.modify:
        binary, find, replace = settings.modify
        if not exists(binary):
            die('Error: {file} not found'.format(file=binary))

        Log.w('Modifying: {bin}'.format(bin=binary))

        with open(binary, 'r') as f:
            content = f.read()

        if find.decode('hex') not in content:
            die('Error: String {find} not found in the file'.format(find=find))

        if content.find(find.decode('hex')) != content.rfind(find.decode('hex')):
            die('Error: More than one instance of {find} was found.'.format(find=find))

        Log.w('Backing up file to {file}.bk'.format(file=binary))
        with open('{file}.bk'.format(file=binary), 'w') as f:
            f.write(content)

        Log.w('Replacing {file}'.format(file=binary))
        with open(binary, 'w') as f:
            f.write(content.replace(find.decode('hex'), replace.decode('hex')))

        return

    iosutils = IOSUtils()
    iosutils.start_tcp_relay()

    if not iosutils.check_dependencies('connection', True):
        die('Error: No connection to the device.')

    if settings.ipa:
        settings.app = iosutils.install(settings.ipa)

    if settings.install:
        iosutils.install(settings.install)

    elif settings.unproxy:
        if not iosutils.check_dependencies('activator', True, True):
            die('Error: Missing dependency - activator.')

        iosutils.set_proxy()

    elif settings.proxy:
        if not iosutils.check_dependencies('activator', True, True):
            die('Error: Missing dependency - activator.')

        iosutils.set_proxy(settings.proxy[0], int(settings.proxy[1]))

    elif settings.update:
        iosutils.update_apps_list()
        iosutils.list_apps()

    elif settings.runchecks:
        iosutils.check_dependencies('full', install=True)

    elif settings.listapps:
        iosutils.list_apps()

    elif settings.app:
        iosanalysis = IOSAnalysis(utils=iosutils, app=settings.app)
        settings.results = iosanalysis.run_analysis()

        if not settings.SILENT:
            Report.report_to_terminal()

        if settings.results:
            if not exists(settings.output):
                makedirs(settings.output)
            Report.report_to_json(iosanalysis.APP_BIN)

    else:
        die('Error: No IPA or APP specified.')

    iosutils.stop_tcp_relay()

def run_android():

        androidutils = AndroidUtils()
        devices = androidutils.devices()
        if settings.runchecks:
            androidutils.check_dependencies('full', silent=False)
            androidutils.clean()
            die()

        if not settings.static and len(devices) == 0:
            die('Error: No devices connected.')
        settings.device = settings.device or (devices[0] if devices else None)
        androidutils.set_device(settings.device)

        REPORT = False
        # fixes problems with APK files in same folder
        if settings.apk and '/' not in settings.apk:
            settings.apk = './{apk}'.format(apk=settings.apk)

        if settings.listapps:
            androidutils.list_apps()

        elif settings.compile:
            androidutils.check_dependencies(['apktool', 'signing'], silent=True)
            androidutils.compile(settings.compile)

        # static only
        elif settings.static and settings.apk:
            androidanalysis = AndroidAnalysis(androidutils, apk=settings.apk)
            settings.results = androidanalysis.run_analysis('static')
            REPORT = True

        else:

            if settings.static and settings.package:
                androidanalysis = AndroidAnalysis(androidutils, package=settings.package)
                settings.results = androidanalysis.run_analysis('static')
                REPORT = True

            elif settings.apk or settings.package:

                if not androidutils.online(settings.device):
                    die('Error: Device {device} not found online'.format(device=settings.device))

                androidanalysis = AndroidAnalysis(androidutils, apk=settings.apk, package=settings.package)
                settings.results = androidanalysis.run_analysis()

                REPORT = True

            else:
                androidutils.clean()
                die('Error: No APK or Package specified.')

        androidutils.clean()

        if REPORT and not settings.SILENT:
            Report.report_to_terminal()

        if REPORT and settings.results:
            if not exists(settings.output):
                makedirs(settings.output)
            Report.report_to_json(androidanalysis.PACKAGE)

def run():
    import traceback

    if settings.jsonprint:
        with open(settings.jsonprint, 'r') as f:
            for i in loads(f.read())['issues']:
                issue = ReportIssue.load(i)
                issue.print_issue()
        exit(0)

    if settings.type == 'ios':
        try:
            run_ios()
        except Exception as e:
            Log.d(traceback.format_exc())
            die('Error: {error}'.format(error=e))

    elif settings.type == 'android':
        try:
            run_android()
        except Exception as e:
            Log.d(traceback.format_exc())
            die('Error: {error}'.format(error=e))


def main():
    parse_arguments()
    run()

def default():
    find_executables()
    merge_settings()

default()
if __name__ == '__main__':
    main()

"""
# TESTS
import mat; mat.settings.output = "/tmp/mat-tests/mat-output"; iosutils = mat.IOSUtils(); iosa = mat.IOSAnalysis(iosutils, ipa='/tmp/mat-tests/MyBanking.ipa');
import mat; mat.settings.output = "/tmp/mat-tests/mat-output"; mat.settings.apk = "/tmp/mat-tests/mybanking.apk"; mat.settings.device = "00cd7e67ec57c127"; androidutils = mat.AndroidUtils(); androida = mat.AndroidAnalysis(androidutils, apk=mat.settings.apk);

import mat; mat.settings.output = "/tmp/mat-tests/mat-output"; iosutils = mat.IOSUtils(); iosa = mat.IOSAnalysis(iosutils, ipa='/tmp/mat-tests/MyBanking.ipa'); r = iosa.run_analysis()
import mat; mat.settings.output = "/tmp/mat-tests/mat-output"; mat.settings.apk = "/tmp/mat-tests/mybanking.apk"; mat.settings.device = "00cd7e67ec57c127"; androidutils = mat.AndroidUtils(); androida = mat.AndroidAnalysis(androidutils, apk=mat.settings.apk); r = androida.run_analysis()


from modules.ios.static.arc_support import Issue; a = Issue(iosa); a.run()
from modules.ios.dynamic.excessive_permissions import Issue; a = Issue(iosa); a.run()

from android.dynamic.drozer_pathtraversal import Issue; a = Issue(androidanalysis); a.dependencies()


mkdir /tmp/mat-tests; cp /work/misc/MyBanking/OLD-Versions/mybanking-1.0.4.apk /tmp/mat-tests/mybanking.apk
mkdir /tmp/mat-tests; cp /work/dev/ios/MyBanking/MyBanking.ipa /tmp/mat-tests

androidutils.clean()
iosutils.clean()

import mat; mat.settings.output = "/tmp/mat-tests/mat-output"; iosutils = mat.IOSUtils(); iosa = mat.IOSAnalysis(iosutils, ipa='/tmp/mat-tests/MyBanking.ipa'); r = iosa.run_static_checks()

"""