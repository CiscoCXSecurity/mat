#!/usr/bin/python
# -*- coding: utf-8 -*-

# system modules
from json import loads
from sys import argv, exit, path
from os import getenv, makedirs
from os.path import exists
import argparse

#local modules
import settings
from utils import Utils, Log, die, AndroidUtils, ADB, IOSUtils
from report import Report, Issue

# android imports
from android import AndroidAnalysis
from ios import IOSAnalysis

"""
TODO LIST

* Add proxy setup on android: https://github.com/jpkrause/AndroidProxySetter
* Finish proxy over usb
* Add interactive mode
* Finish Cordova features check
"""

VERSION = '2.1.5'

LOCAL_SETTINGS = "{home}/.config/audits".format(home=getenv('HOME'))

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
    '''.format(version=VERSION, lsettings=LOCAL_SETTINGS)

def findExecutables():
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
    settings.android     = Utils.run('which android')[0].split('\n')[0]

    # ios expect shell
    settings.expect     = Utils.run('which expect')[0].split('\n')[0]

def mergeSettings():
    path.append(LOCAL_SETTINGS)
    try:
        import mat_settings

        # emulator settings
        settings.avd         = mat_settings.avd         if hasattr(mat_settings, 'avd')         else settings.avd

        # boolean / test settings
        settings.device      = mat_settings.device      if hasattr(mat_settings, 'device')      else settings.device
        settings.SILENT      = mat_settings.SILENT      if hasattr(mat_settings, 'SILENT')      else settings.SILENT
        settings.DEBUG       = mat_settings.DEBUG       if hasattr(mat_settings, 'DEBUG')       else settings.DEBUG

        # static analysis settings
        settings.minsdk      = mat_settings.minsdk      if hasattr(mat_settings, 'minsdk')      else settings.minsdk
        settings.targetsdk   = mat_settings.targetsdk   if hasattr(mat_settings, 'targetsdk')   else settings.targetsdk
        settings.maxsdk      = mat_settings.maxsdk      if hasattr(mat_settings, 'maxsdk')      else settings.maxsdk

        # Merge the rest of the settings
        settings.ANDROID_PERMISSIONS = list(set(settings.ANDROID_PERMISSIONS + mat_settings.ANDROID_PERMISSIONS)) if hasattr(mat_settings, 'ANDROID_PERMISSIONS') else settings.ANDROID_PERMISSIONS
        settings.IOS_PERMISSIONS = list(set(settings.IOS_PERMISSIONS + mat_settings.IOS_PERMISSIONS)) if hasattr(mat_settings, 'IOS_PERMISSIONS') else settings.IOS_PERMISSIONS

        if hasattr(mat_settings, 'ANDROID_ISSUES'):
            for issue in  mat_settings.ANDROID_ISSUES:
                settings.ANDROID_ISSUES[issue] = mat_settings.ANDROID_ISSUES[issue]

        if hasattr(mat_settings, 'IOS_ISSUES'):
            for issue in  mat_settings.IOS_ISSUES:
                settings.IOS_ISSUES[issue] = mat_settings.IOS_ISSUES[issue]

        if hasattr(mat_settings, 'CORDOVA_ISSUES'):
            for issue in  mat_settings.CORDOVA_ISSUES:
                settings.CORDOVA_ISSUES[issue] = mat_settings.CORDOVA_ISSUES[issue]

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

    # TO IMPLEMENT
    androidparser.add_argument('-p', '--set-proxy',    required=False, metavar='ip:port',                                      help='[NOT WORKING ON 6.0+] Sets up a proxy on Android settings')
    androidparser.add_argument('-P', '--unset-proxy',  required=False, default=False, action='store_true',                     help='[NOT WORKING ON 6.0+] Unsets the proxy on Android settings')

    # REFACTORED
    androidparser.add_argument('-l', '--list-apps',    required=False, default=False, action='store_true',                     help='Lists the Android applications installed that can be assessed')
    androidparser.add_argument('-g', '--compile',      required=False, metavar='/path/to/decompiled/',                         help='Specify the decompiled app to compile and sign')

    androidparser.add_argument('-n', '--no-install',   required=False, default=False, action='store_true',                     help='Uninstalls the application after the dynamic analysis')
    androidparser.add_argument('-k', '--no-keep',      required=False, default=False, action='store_true',                     help='Deletes the decompiled APK and all data after static analysis')

    androidparser.add_argument('-r', '--run-checks',   required=False, default=False, action='store_true',                     help='Performs dependency checks for Android')
    androidparser.add_argument('-o', '--output',       required=False, metavar='/path/to/',                                    help='Folder to where the tool will report')

    return parser.parse_args()

def parseArguments():
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
    settings.proxy       = args.set_proxy.split(':', 1) if args.set_proxy else None
    settings.unproxy     = args.unset_proxy

    # ios args
    if settings.type == 'ios':
        settings.app     = args.app
        settings.ipa     = args.ipa
        settings.install = args.install
        settings.update  = args.update_apps
        settings.modify  = args.modify

    # android args
    if settings.type == 'android':
        settings.static  = args.static_only
        settings.device  = args.device or settings.device
        settings.avd     = args.avd or settings.avd
        settings.apk     = args.apk
        settings.package = args.package
        settings.compile = args.compile

def runIOS():
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
    iosutils.startTCPRelay()

    if not iosutils.checkDependencies('connection', True):
        die('Error: No connection to the device.')

    if settings.ipa:
        settings.app = iosutils.install(settings.ipa)

    if settings.install:
        iosutils.install(settings.install)

    elif settings.unproxy:
        if not iosutils.checkDependencies('activator', True, True):
            die('Error: Missing dependency - activator.')

        iosutils.setProxy()

    elif settings.proxy:
        if not iosutils.checkDependencies('activator', True, True):
            die('Error: Missing dependency - activator.')

        iosutils.setProxy(settings.proxy[0], int(settings.proxy[1]))

    elif settings.update:
        iosutils.updateAppsList()
        iosutils.listApps()

    elif settings.runchecks:
        iosutils.checkDependencies('full', install=True)

    elif settings.listapps:
        iosutils.listApps()

    elif settings.app:
        ia = IOSAnalysis(settings.app, iosutils)
        ia.runAnalysis()

        if not settings.SILENT:
            Report.reportToTerminal()

        if settings.results:
            if not exists(settings.output):
                makedirs(settings.output)
            Report.reportToJson(ia.APP_BIN)

    else:
        die('Error: No IPA or APP specified.')

    iosutils.stopTCPRelay()

def runAndroid():
        # check devices
        adb = ADB(adb=settings.adb)

        androidutils = AndroidUtils(adb=adb)
        adb.startServer()
        devices = adb.devices()
        if settings.runchecks:
            androidutils.checkDependencies('full')
            adb.stopServer()
            die()

        if not settings.static and len(devices) == 0:
            die('Error: No devices connected.')
        settings.device = settings.device or (devices[0] if devices else None)
        adb.setDevice(settings.device)
        adb.makeTempFolder()

        REPORT = False
        # fixes problems with APK files in same folder
        if settings.apk and '/' not in settings.apk:
            settings.apk = './{apk}'.format(apk=settings.apk)


        if settings.listapps:
            androidutils.listApps()

        elif settings.compile:
            androidutils.checkDependencies(['apktool', 'signing'], silent=True)
            androidutils.compile(settings.compile)

        # static only
        elif settings.static and settings.apk:
            aa = AndroidAnalysis(androidutils, apk=settings.apk, adb=adb)
            aa.runAnalysis('static')
            REPORT = True

        else:
            if settings.proxy:
                if not androidutils.checkDependencies('proxy', silent=True, install=True):
                    die('Error: Missing dependency - proxy-setter.')

                #androidutils.setProxy(settings.device, settings.proxy[0], int(settings.proxy[1]))

            elif settings.unproxy:
                if not androidutils.checkDependencies('proxy', silent=False, install=True):
                    die('Error: Missing dependency - proxy-setter.')

                #androidutils.setProxy(settings.device)

            elif settings.static and settings.package:
                aa = AndroidAnalysis(androidutils, package=settings.package, adb=adb)
                aa.runAnalysis('static')
                REPORT = True

            elif settings.apk or settings.package:

                if not adb.online(settings.device):
                    die('Error: Device {device} not found online'.format(device=settings.device))

                aa = AndroidAnalysis(androidutils, apk=settings.apk, package=settings.package, adb=adb)
                aa.runAnalysis()

                REPORT = True
                adb.stopServer()

            else:
                die('Error: No APK or Package specified.')

        #adb.clean()

        if REPORT and not settings.SILENT:
            Report.reportToTerminal()

        if REPORT and settings.results:
            if not exists(settings.output):
                makedirs(settings.output)
            Report.reportToJson(aa.PACKAGE)

def run():
    if settings.jsonprint:
        with open(settings.jsonprint, 'r') as f:
            for i in loads(f.read())['issues']:
                issue = Issue.load(i)
                issue.print_issue()
        exit(0)

    if settings.type == 'ios':
        runIOS()

    elif settings.type == 'android':
        runAndroid()

def main():
    findExecutables()
    mergeSettings()

    parseArguments()
    run()

if __name__ == "__main__":
    main()

