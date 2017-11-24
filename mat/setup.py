#! /usr/bin/env python
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools import setup, find_packages
from os import path, makedirs, chmod
from shutil import copy

from mat.utils import settings

file_path = path.realpath(__file__).rsplit('/', 1)[0]

CONFIG_FOLDER     = settings.LOCAL_SETTINGS
LIB_FOLDER        = '{config}/lib'.format(config=CONFIG_FOLDER)
LIB_SUBFOLDERS    = ['{lib}/dex2jar'.format(lib=LIB_FOLDER), '{lib}/dex2jar/lib'.format(lib=LIB_FOLDER), '{lib}/signing'.format(lib=LIB_FOLDER)]
LIB_FILES         = [
    'apktool', 'apktool.jar', 'dex2jar/d2j-dex2jar.bat',
    'dex2jar/d2j-dex2jar.sh', 'dex2jar/d2j_invoke.bat', 'dex2jar/d2j_invoke.sh',
    'dex2jar/lib/antlr-runtime-3.5.jar', 'dex2jar/lib/asm-debug-all-4.1.jar',
    'dex2jar/lib/d2j-base-cmd-2.0.jar', 'dex2jar/lib/d2j-jasmin-2.0.jar',
    'dex2jar/lib/d2j-smali-2.0.jar', 'dex2jar/lib/dex-ir-2.0.jar',
    'dex2jar/lib/dex-reader-2.0.jar', 'dex2jar/lib/dex-reader-api-2.0.jar',
    'dex2jar/lib/dex-tools-2.0.jar', 'dex2jar/lib/dex-translator-2.0.jar',
    'dex2jar/lib/dex-writer-2.0.jar', 'dex2jar/lib/dx-1.7.jar',
    'dump_fileprotection', 'dump_log', 'dumpdecrypted.dylib', 'jd-cli',
    'jd-cli.jar', 'scptoios', 'signing/cert.x509.pem', 'signing/key.pk8',
    'signing/signapk.jar', 'sshios',
    'scpfromios', 'keychain_dump',
    'busybox', 'backup_excluded'
]

MODULES = [
    'modules/ios/static', 'modules/ios/dynamic',
    'modules/android/static', 'modules/android/dynamic',
    'modules/cordova/static'
]

SETTINGS_FILENAME = '{config}/mat_settings.py'.format(config=CONFIG_FOLDER)
DEFAULT_SETTINGS="""# Default Settings if no options are provided to MAT (all optional)

#device    = 'emulator-1234'

#SILENT    = False
DEBUG      = {debug}

# avd settings
#avd     = 'Testing-AVD-Name'
"""

def common(debug=False):
    global SETTINGS_FILENAME

    if not path.exists(CONFIG_FOLDER):
        try:
            makedirs(CONFIG_FOLDER)
            if not path.exists(CONFIG_FOLDER):
                raise OSError()
        except OSError:
            print('[-] No permission to create {config}.'.format(config=CONFIG_FOLDER))
            exit(0)

    for folder in MODULES:
        folder = '{root}/{folder}'.format(root=CONFIG_FOLDER, folder=folder)
        if not path.exists(folder):
            try:
                makedirs(folder)
                if not path.exists(folder):
                    raise OSError()
            except OSError:
                print('[-] No permission to create {config}.'.format(config=folder))
                exit(0)

    # check if lib folders exist and can be created
    for folder in LIB_SUBFOLDERS:
        if not path.exists(folder):
            try:
                makedirs(folder)
                if not path.exists(folder):
                    raise OSError()
            except OSError:
                print('[-] No permission to create {lib}.'.format(lib=folder))
                exit(0)

    # copy lib files to $HOME/.config/audits/lib/
    for file in LIB_FILES:
        copy('lib/{file}'.format(file=file), "{lib}/{file}".format(lib=LIB_FOLDER, file=file))
        if not path.exists("{lib}/{file}".format(lib=LIB_FOLDER, file=file)):
            print('[-] Failed to copy file {file} to {lib}'.format(lib=LIB_FOLDER, file=file))
            exit(0)
        chmod("{lib}/{file}".format(lib=LIB_FOLDER, file=file), 0744)


    # copy template to place
    if path.exists(SETTINGS_FILENAME):
        SETTINGS_FILENAME = '{lsettings}_{version}.py'.format(lsettings=SETTINGS_FILENAME.replace(".py", ""), version=settings._VERSION.replace(".", ""))

    # creating default settings
    with open(SETTINGS_FILENAME, 'w') as w:
        w.write(str(DEFAULT_SETTINGS).replace('{debug}', ("True" if debug else "False")))
        if not path.exists(SETTINGS_FILENAME):
            print('[-] Failed to create {file}'.format(file=SETTINGS_FILENAME))
            exit(0)
        print('[+] {lsettings} created.'.format(lsettings=SETTINGS_FILENAME))

class _pre_install(install):
    def run(self):
        common(debug=False)
        install.run(self)

class _pre_develop(develop):
    def run(self):
        common(debug=True)
        develop.run(self)

setup(
    name="mat",
    version=settings._VERSION,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'mat = mat:main'
        ]
    },
    cmdclass={
        'install': _pre_install,
        'develop': _pre_develop,
    },
    author='Ruben de Campos',
    author_email='rdc@65535.com',
    description='Mobile Assessment Tool',
    keywords=['android', 'ios', 'cordova', 'static assessment', 'dynamic assessment', 'mobile assessments', 'apk', 'ipa', 'security'],
    long_description="""
        Tool to perform static and dynamic checks on android and ios applications.
    """
)