# Mobile Assessment Tool #

Mobile Assessment Tool or MAT is a tool that automatises an Android or IOS application assessment by performing some static and dynamic checks and producing a JSON report in the end.

The json report can be imported to XDB using the mat import module.

[Imcomplete] Documentation generated with PDOC: https://github.com/BurntSushi/pdoc

## Installation ##

```
cd mat
python setup.py install
```

## Configuration ##

By default several checks are already in place but custom checks can also be added on the local settings file located by default under:
```
~/.mat/mat_settings.py
```

A template of all the settings that can be changed is already in place at the location mentioned above.

## Usage ##

```
usage: mat [-h] [-S] [-D] [-J file] {ios,android} ...

          __  __     _   _____
         |  \/  |   / \ |_   _|
         | |\/| |  / _ \  | |
         | |  | | / ___ \ | |
         |_|  |_|/_/   \_\|_|
                    Mobile Assessment Tool v3.1.3

  Copyright 2017 - Portcullis, https://www.portcullis-security.com

  Your local settings will be under /Users/user/.mat/mat_settings.py.

optional arguments:
  -h, --help            show this help message and exit
  -S, --silent          Does not ouput any information to the console aside
                        from errors
  -D, --debug           Verbose mode, displays debug information as well
  -J file, --json-print file
                        Prints the isses from the json file provided

subcommands:
  Select the type of assessment

  {ios,android}

usage: mat android [-h] [-i apk_file] [-a com.package.app] [-s] [-d device]
                   [-e avd] [-l] [-g /path/to/decompiled/] [-n] [-k] [-r]
                   [-o /path/to/output]

optional arguments:
  -h, --help            show this help message and exit
  -i apk_file, --apk apk_file
                        Specify the APK file to be analysed
  -a com.package.app, --package com.package.app
                        Specify the PACKAGE to be analysed
  -s, --static-only     Perform static analysis only
  -d device, --device device
                        Specify the device to install the apk
  -e avd, --avd avd     Specify the AVD emulator image name
  -l, --list-apps       Lists the Android applications installed that can be
                        assessed
  -g /path/to/decompiled/, --compile /path/to/decompiled/
                        Specify the decompiled app to compile and sign
  -n, --no-install      Uninstalls the application after the dynamic analysis
  -k, --no-keep         Deletes the decompiled APK and all data after static
                        analysis
  -r, --run-checks      Performs dependency checks for Android
  -o /path/to/, --output /path/to/
                        Folder to where the tool will report

usage: mat ios [-h] [-a id] [-i /path/to/file.ipa] [-s] [-I /path/to/file.ipa]
               [-m binary hex_find hex_replace] [-n] [-k] [-r] [-o /path/to/output]
               [-u] [-l] [-p ip:port] [-P]

optional arguments:
  -h, --help            show this help message and exit
  -a id, --app id       Installed APP id to be tested
  -i /path/to/file.ipa, --ipa /path/to/file.ipa
                        IPA file to install and analyse
  -s, --static-only     Perform static analysis only
  -I /path/to/file.ipa, --install /path/to/file.ipa
                        IPA file to just install
  -m binary hex_find hex_replace, --modify binary hex_find hex_replace
                        Finds and replaces the binary instructions on the
                        provided binary
  -n, --no-install      Uninstalls the app once the analysis is completed
                        (only when `-i` is used).
  -k, --no-keep         Deletes the local data (decrypted binary, pulled IPA,
                        data files, classes, etc.) once the analysis is
                        complete
  -r, --run-checks      Performs dependency checks for iOS
  -o /path/to/, --output /path/to/
                        Folder to where the tool will report
  -u, --update-apps     Update iOS applications list
  -l, --list-apps       Lists the iOS applications installed that can be
                        assessed
  -p ip:port, --set-proxy ip:port
                        Sets up a proxy on iOS preferences
  -P, --unset-proxy     Unsets the proxy on iOS preferences
```

## Examples ##


* Static analysis of Android Application and save the results to /tmp/tests/
```
$ mat ios -s -i /tmp/myapp.apk -o /tmp/tests
```

* Full analysis of iOS Application installed on connected the device
```
$ mat ios -s -a com.csco.example
```

* Listing apps installed on iOS with DEBUG enabled - show all the commands run
```
$ mat -D ios -l
```

* Check if all requirements are ok for android
```
$ mat android -r
```

* Print all the details of a previous test
```
$ mat -J /tmp/tests/com.csco.example.json android
```

## Import Examples ##

* Import mat and run requirements checks for android
```
In [1]: import mat

In [2]: androidutils = mat.AndroidUtils()

In [3]: result = androidutils.check_dependencies(silent=True)

In [4]: print result
True
```

* Import mat and run dynamic checks on an iOS app, wirting the output to /tmp/output
```
In [1]: import mat

In [2]: mat.settings.output = '/tmp/output'

In [3]: iosutils = mat.IOSUtils();

In [4]: iosa = mat.IOSAnalysis(iosutils, ipa='./example.ipa');
[W](2017-08-17 14:23:31) ios.__init__                     : Creating Analysis for: None / ./example.ipa
[W](2017-08-17 14:23:31) ios.prepare_analysis             : Preparing iOS Analysis
[E](2017-08-17 14:23:33) ios.list_apps                    : Error: Device OS not supported - backporting to old methods

In [5]: iosa.run_dynamic_checks()
Out[5]:
[<mat.modules.ios.dynamic.excessive_permissions.Issue at 0x1107da110>,
 <mat.modules.ios.dynamic.file_protection.Issue at 0x1107da350>]
```

* Test a specific iOS issue
```
In [1]: import mat

In [2]: androidutils = mat.AndroidUtils()
[E](2017-08-17 14:31:51) android.__init__                 : Error: No devices connected.
[E](2017-08-17 14:31:51) android._run_on_device           : Error: No device connected. Could not run: shell su -c mkdir /sdcard/mat-tmp

In [3]: androida = mat.AndroidAnalysis(androidutils, apk='./example.apk');
[W](2017-08-17 14:32:13) android.__init__                 : Creating Analysis for: None / ./example.apk
[W](2017-08-17 14:32:13) android.prepare_analysis         : Preparing Android Analysis
[E](2017-08-17 14:32:13) android.prepare_analysis         : Error: Dependencies not met, run `-r` for more details
[W](2017-08-17 14:32:13) android.prepare_analysis         : Decompiling mat-output/android-example/example.apk to mat-output/android-example/decompiled-app
[W](2017-08-17 14:32:16) android.prepare_analysis         : Converting mat-output/android-example/example.apk classes to mat-output/android-example/com.pcsl.mybanking.jar

In [4]: from mat.modules.android.static import logcat

In [5]: issue = logcat.Issue(androida)

In [6]: issue.dependencies()
Out[6]: True

In [7]: issue.run()

In [8]: print issue.REPORT
True
```

* Test a custom issue
```
In [1]: import mat

In [2]: iosutils = mat.IOSUtils();

In [3]: iosa = mat.IOSAnalysis(iosutils, ipa='./example.ipa');
[W](2017-08-17 14:53:45) ios.__init__                     : Creating Analysis for: None / ./example.ipa
[W](2017-08-17 14:53:45) ios.prepare_analysis             : Preparing iOS Analysis
[E](2017-08-17 14:53:47) ios.list_apps                    : Error: Device OS not supported - backporting to old methods

In [4]: modules = iosa.get_custom_modules()

In [5]: print modules
[<module 'example' from '/Users/user/.mat/modules/ios/static/example.py'>, <module 'example2' from '/Users/user/.mat/modules/ios/static/example2.py'>]

In [6]: check = modules[0]

In [7]: issue = check.Issue(iosa)

In [8]: issue.dependencies()
Out[8]: True

In [9]: issue.run()

In [10]: issue.DETAILS
Out[10]: ('Darwin\r\n', '')

In [11]: issue.REPORT
Out[11]: True
```

## Future Work ##

* Add interactive mode
* Finish Cordova features check
* Change drozer checks for manual checks (remove drozer dependency)
* Add code obfuscation detection
* Improve documentation