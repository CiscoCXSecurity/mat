#system modules
from os import path

# local modules
from report import Issue
from utils import Utils, Log, die
import settings

class CordovaAnalysis(object):

    LATEST_VERSION_URL = 'https://dist.apache.org/repos/dist/release/cordova/platforms/'
    LATEST_VERSION = {
        'ios':     '4.3.1',
        'android': '6.2.0',
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

    def prepareAnalysis(self):
        Log.w('Getting latest cordova versions')

        import urllib2
        response = urllib2.urlopen(CordovaAnalysis.LATEST_VERSION_URL)
        html = response.read()
        for os in  CordovaAnalysis.LATEST_VERSION:
            self.LATEST_VERSION[os] = html.split('-{os}-'.format(os=os))[1].rsplit('.', 1)[0]

    def reportIssues(self):
        Log.w('Reporting Findings')

        if self.CORDOVA_VERSION and self.CORDOVA_VERSION < self.LATEST_VERSION[self.ASSESSMENT_TYPE]:
            details = '<code>{version}</code>'.format(version=self.CORDOVA_VERSION_DETAILS)
            settings.results.append(Issue(settings.CORDOVA_ISSUES['outdated']['title'], settings.CORDOVA_ISSUES['outdated']['issue-id'], '', details))

        if self.TODO:
            details = '<code>{todo}</code>'.format(todo='\n'.join(self.TODO))
            settings.results.append(Issue(settings.CORDOVA_ISSUES['todo']['title'], settings.CORDOVA_ISSUES['todo']['issue-id'], '', details))

        if self.OPEN_ORIGIN:
            details = '<code>{open}</code>'.format(open=self.OPEN_ORIGIN)
            settings.results.append(Issue(settings.CORDOVA_ISSUES['open']['title'], settings.CORDOVA_ISSUES['open']['issue-id'], '', details))

        # TODO: not reporting self.FEATURES just yet - need to check which are actually dangerous

    def runAnalysis(self):
        Log.w('Starting Analysis.')
        self.prepareAnalysis()

        if not self.CONFIG_FILE and not self.CORDOVA_FILE:
            Log.w('No cordova files found.')
            return False

        self.CORDOVA_VERSION, self.TODO, self.FEATURES, self.OPEN_ORIGIN = None, [], [], None

        if self.CORDOVA_FILE:
            with open(self.CORDOVA_FILE, 'r') as f:
                cordova = f.read()

            for line in cordova.split('\n'):
                if ('CORDOVA_JS_BUILD_LABEL' in line or 'PLATFORM_VERSION_BUILD_LABEL' in line) and '\'' in line:
                    self.CORDOVA_VERSION = line.split('\'')[1].strip()
                    self.CORDOVA_VERSION_DETAILS = line

                if 'TODO:' in line:
                    self.TODO += [line.strip()]

        if self.CONFIG_FILE:
            with open(self.CONFIG_FILE, 'r') as f:
                config = f.read()

            for line in config.split('\n'):
                if '<feature name=' in line:
                    self.FEATURES += [line.strip()]

                if '<access origin="*"' in line:
                    self.OPEN_ORIGIN = line.strip()


        self.reportIssues()
