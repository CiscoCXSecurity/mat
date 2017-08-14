# Mobile Assessment Tool #

Mobile Assessment Tool or MAT is a tool that automatises an Android or IOS application assessment by performing some static and dynamic checks and producing a JSON report in the end.

The json report can be imported to XDB using the pdatool import module.

Doc generated with PDOC: https://github.com/BurntSushi/pdoc

## Installation ##

```
#!bash

cd mat
python setup.py install
```

## Configuration ##

By default several checks are already in place but costume checks can also be added on the local settings file located by default under:
```
#!bash

~/.config/audits/mat_settings.py
```

A template of all the settings that can be changed is already in place at the location mentioned above.

## Examples of Usage ##

```
#!bash

$ mat -h
usage: mat [-h] [-S] [-D] [-J file] {ios,android} ...

          _____           _             _ _ _
         |  __ \         | |           | | (_)
         | |__) |__  _ __| |_ ___ _   _| | |_ ___
         |  ___/ _ \| '__| __/ __| | | | | | / __|
         | |  | (_) | |  | || (__| |_| | | | \__ \
         |_|   \___/|_|   \__\___|\__,_|_|_|_|___/  Security

                          Mobile Assessment Tool v2.0.0

  Copyright 2016 - Portcullis, https://www.portcullis-security.com

  Your local settings will be under /Users/ruben/.config/audits/mat_settings.py.


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

Example of usage:
    mat -D ios -a com.apple.TestFlight
    mat android -a /tmp/app.apk -o /tmp/mat-output -s -d
    mat -J json_file android

$ mat ios -h
usage: mat ios [-h] [-l] [-a id] [-i /path/to/file.ipa] [-n] [-k] [-r]
               [-o /path/to/]

optional arguments:
  -h, --help            show this help message and exit
  -l, --list-apps       Lists the iOS applications installed that can be
                        assessed
  -a id, --app id       Installed APP id to be tested
  -i /path/to/file.ipa, --ipa /path/to/file.ipa
                        IPA file to install and analyse
  -n, --no-install      Uninstalls the app once the analysis is completed
                        (only when `-i` is used).
  -k, --no-keep         Deletes the local data (decrypted binary, pulled IPA,
                        data files, classes, etc.) once the analysis is
                        complete
  -r, --run-checks      Performs dependency checks for iOS
  -o /path/to/, --output /path/to/
                        Folder to where the tool will report

mat android -h
usage: mat android [-h] [-s] [-d] [-n] [-c] [-i device] [-e avd] [-a apk_file]
                   [-p com.package.app] [-g file] [-r] [-o /path/to/]

optional arguments:
  -h, --help            show this help message and exit
  -s, --static          Perform static analysis
  -d, --dynamic         Perform dynamic analysis
  -n, --no-install      Uninstalls the application after the dynamic analysis
  -c, --no-decompile    Deletes the decompiled APK after static analysis
  -i device, --device device
                        Specify the device to install the apk
  -e avd, --emulator avd
                        Specify the AVD emulator image name
  -a apk_file, --apk apk_file
                        Specify the APK file to be analysed
  -p com.package.app, --package com.package.app
                        Specify the PACKAGE to be analysed
  -g file, --sign file  Specify the decompiled app to compile and sign
  -r, --run-checks      Performs dependency checks for Android
  -o /path/to/, --output /path/to/
                        Folder to where the tool will report


```