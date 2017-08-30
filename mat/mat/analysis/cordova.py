#system modules
from os import path

# dynamic load modules
from os import listdir
from imp import load_source

# local modules
from mat.utils.utils import Utils, Log
from mat.utils import settings

class CordovaAnalysis(object):

    LATEST_VERSION_URL = 'https://dist.apache.org/repos/dist/release/cordova/platforms/'
    LATEST_VERSION = {
        'ios':     '4.4.0',
        'android': '6.2.3',
    }

    LOCATIONS      = {
        'config':  ['config.xml', 'res/xml/config.xml'],
        'cordova': ['cordova.js', 'assets/www/cordova.js'],
        'www':     ['www',        'assets/www']
    }

    def __init__(self, root=None, data=None, atype=None, config=None, cordova=None):

        self.ASSESSMENT_TYPE = atype
        self.ROOT            = root
        self.CONFIG_FILE     = config
        self.CORDOVA_FILE    = cordova

        if self.ROOT and not self.CONFIG_FILE:
            for location in CordovaAnalysis.LOCATIONS['config']:
                if path.exists('{root}/{loc}'.format(root=self.ROOT, loc=location)):
                    self.CONFIG_FILE = '{root}/{loc}'.format(root=self.ROOT, loc=location)
                    break

        if self.ROOT and not self.CORDOVA_FILE:
            for location in CordovaAnalysis.LOCATIONS['cordova']:
                if path.exists('{root}/{loc}'.format(root=self.ROOT, loc=location)):
                    self.CORDOVA_FILE = '{root}/{loc}'.format(root=self.ROOT, loc=location)
                    break

        if not self.CORDOVA_FILE and data:
            self.CORDOVA_FILE = Utils.run('find {data} -name cordova.js'.format(data=data))[0].split('\n')[0].strip()

        if not self.CONFIG_FILE and self.ROOT:
            self.CONFIG_FILE = Utils.run('find {root} -name config.xml'.format(root=self.ROOT))[0].split('\n')[0].strip()

        Log.d('Root: {fpath}'.format(fpath=self.ROOT))
        Log.d('cordova.js: {fpath}'.format(fpath=self.CORDOVA_FILE))
        Log.d('config.xml: {fpath}'.format(fpath=self.CONFIG_FILE))

    def found(self):
        return self.CONFIG_FILE or self.CORDOVA_FILE

    def prepare_analysis(self):
        Log.w('Getting latest cordova versions')

        import urllib2
        response = urllib2.urlopen(CordovaAnalysis.LATEST_VERSION_URL)
        html = response.read()
        for os in CordovaAnalysis.LATEST_VERSION:
            self.LATEST_VERSION[os] = html.split('-{os}-'.format(os=os))[1].rsplit('.', 1)[0]

    def get_custom_modules(self, modules_types=['modules/cordova/static', 'modules/cordova/dynamic']):
        found_modules = []
        for module_type in modules_types:
            modules = [m.replace('.py', '') for m in listdir('{local}/{type}'.format(local=settings.LOCAL_SETTINGS, type=module_type)) if not m.endswith('.pyc')]
            for m in modules:
                found_modules += [load_source(m, '{local}/{type}/{check}.py'.format(local=settings.LOCAL_SETTINGS, type=module_type, check=m))]
        return found_modules

    def _run_custom_modules(self, module_type):
        issues = []
        modules = self.get_custom_modules([module_type])
        for m in modules:
            Log.d('Running Static {check}'.format(check=m.__name__))
            issue = m.Issue(self)
            if issue.dependencies():
                issue.run()
            else:
                Log.e('Error: Dependencies not met.')
            if issue.REPORT:
                issues += [issue]

        return issues

    def _run_custom_static_analysis(self):
        module_type = 'modules/cordova/static'
        return self._run_custom_modules(module_type)

    def run_analysis(self):
        Log.w('Starting Analysis.')
        self.prepare_analysis()

        if not self.CONFIG_FILE and not self.CORDOVA_FILE:
            Log.w('No cordova files found.')
            return []

        issues = []

        import mat.modules.cordova.static
        static_checks = [m.replace('.py', '') for m in listdir(mat.modules.cordova.static.__path__[0]) if not m.endswith('.pyc') and not m.startswith('__')]
        for check in static_checks:
            Log.d('Running Static {check}'.format(check=check))
            check_module = __import__('mat.modules.cordova.static.{check}'.format(check=check), fromlist=['Issue'])

            issue = check_module.Issue(self)
            if issue.dependencies():
                issue.run()
            else:
                Log.e('Error: Dependencies not met.')
            if issue.REPORT:
                issues += [issue]

        issues += self._run_custom_static_analysis()

        return issues

