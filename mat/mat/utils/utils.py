# python modules
from subprocess import Popen, PIPE
from os import path, remove, walk, rmdir
from sys import exit
import traceback

# local modules
import settings

################################################################################
#    LOG FUNCTIONS
################################################################################

class Log:
    import inspect

    MAX_TAG_SIZE = 32

    @staticmethod
    def _log(t='W', TAG='', MSG=''):
        from time import gmtime, strftime
        now = strftime('%Y-%m-%d %H:%M:%S', gmtime())
        space = Log.MAX_TAG_SIZE - min(Log.MAX_TAG_SIZE, len(TAG))
        print('[{type}]({now}) {tag}{space} : {msg}'.format(now=now, tag=TAG[:Log.MAX_TAG_SIZE], space=' '*space, type=t, msg=MSG))

    @staticmethod
    def write(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('W', TAG, MSG)

    @staticmethod
    def w(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('W', TAG, MSG)

    @staticmethod
    def error(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('E', TAG, MSG)

    @staticmethod
    def e(MSG='', TAG=None):
        if not settings.SILENT:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('E', TAG, MSG)

    @staticmethod
    def debug(MSG='', TAG=None):
        if not settings.SILENT and settings.DEBUG:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('D', TAG, MSG)

    @staticmethod
    def d(MSG='', TAG=None):
        if not settings.SILENT and settings.DEBUG:
            TAG = TAG or '{module}.{tag}'.format(tag=Log.inspect.stack()[1][3], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[-1])
            Log._log('D', TAG, MSG)

################################################################################
#    ISSUE OBJECT
################################################################################

class Issue(object):

    TITLE       = "Issue Title"
    DESCRIPTION = "Testing Description"

    ID          = None
    ISSUE_TITLE = None
    FINDINGS    = None

    def __init__(self, analysis):
        self.ANALYSIS = analysis
        self.REPORT   = False
        self.DETAILS  = None

    def dependencies(self):
        self.ANALYSIS.UTILS.check_dependencies(['full'], install=True)

    def run(self):
        return True

################################################################################
#    GENERAL UTILS FUNCTIONS
################################################################################

class Command(object):

    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.std = ('', '')

    def run(self, shell, timeout=1):
        import threading

        def target():
            self.process = Popen(self.cmd, shell=shell, stdout=PIPE, stderr=PIPE)
            self.std = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()

        return self.std

class Utils:

    @staticmethod
    def run(cmd='', shell=False, process=False, timeout=None):
        Log.d('Running: {cmd}'.format(cmd=cmd))

        try:
            cmd = cmd if shell else cmd.split(' ')
            if process:
                return Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)

            if timeout:
                return Command(cmd).run(shell, timeout)

            return Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell).communicate()
        except Exception:
            Log.d(traceback.format_exc())

        return None

    @staticmethod
    def rmtree(top=None):
        if not top:
            return False
        for root, dirs, files in walk(top, topdown=False):
            for name in files:
                remove(path.join(root, name))
            for name in dirs:
                rmdir(path.join(root, name))
        rmdir(top)

    @staticmethod
    def emulator():
        return Utils.run('{emulator} -avd {avd}'.format(emulator=settings.emulator, avd=settings.avd), shell=True, process=True)

    @staticmethod
    def strings_grep_command(command=None, src=None):
        if not command or not src:
            return None
        return Utils.run('{strings} {src} | {grep} {command}'.format(grep=settings.grep, command=command), shell=True)[0]

    @staticmethod
    def grep_command(command=None, source=''):
        if not command:
            return None
        return Utils._grep_results(Utils.run('{grep} {command}'.format(grep=settings.grep, command=command), shell=True)[0], source)

    @staticmethod
    def grep(regex=None, source=None):
        if not regex or not source:
            return None
        return Utils.grep_command('-aREn "{regex}" {src}'.format(regex=regex, src=source), source)

    @staticmethod
    def multiple_grep(*greps):
        if not greps:
            return None
        return Utils._grep_results(Utils.run(' | '.join(['{grep} {command}'.format(grep=settings.grep, command=command) for command in greps]), shell=True)[0], '')

    @staticmethod
    def _grep_results(result, working_path):
        findings = {}
        for line in result.split('\n'):
            if not line or ':' not in line:
                continue

            f, l, d = line.split(':', 2)
            if any([f.replace(working_path, '').startswith(i['pattern']) for i in settings.IGNORE]):
                continue

            #data = 'Line {line}: {code}'.format(line=l.strip(), code=d.strip())
            data = {'line': l.strip(), 'code': d.strip()}
            if f in findings:
                findings[f].append(data)
            else:
                findings[f] = [data]

        return findings

    @staticmethod
    def grep_details(findings, working_path):
        if not findings: return ""
        details = " "
        for f in findings:
            # bypass ignored paths
            if any([f.replace(working_path, '').startswith(i['pattern']) for i in settings.IGNORE]):
                continue

            details = "{details}\n\n* {file}".format(details=details, file=f.replace(working_path,''))[1:]
            findings[f].sort()
            for d in sorted(findings[f], key=lambda k: int(k['line'])):
                details = "{details}\n * Line {line}: {code}".format(details=details, line=d['line'], code=d['code'])

        return details

    @staticmethod
    def ignored_path(fpath=None):
        if not fpath: return False
        for p in settings.IGNORE:
            if p['path'] and p['pattern'] in fpath:
                return True
        return False

    @staticmethod
    def ignored_extension(fpath=None):
        if not fpath: return False
        return '.' in fpath and fpath.rsplit('.', 1)[1].strip() in settings.IGNORED_FILE_EXT

def die(message=''):
    if hasattr(settings, 'tcprelay_process'):
        settings.tcprelay_process.kill()

    if message:
        tag = '{module}.{function}:{line}'.format(function=Log.inspect.stack()[1][3], line=Log.inspect.stack()[1][2], module=Log.inspect.stack()[1][1].replace('.py', '').rsplit('/', 1)[1])
        Log.e(message, tag)
    exit(0)

def methods(object):
    return [method for method in dir(object) if callable(getattr(object, method))]

