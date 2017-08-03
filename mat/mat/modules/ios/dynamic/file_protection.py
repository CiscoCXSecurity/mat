from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'File Protection Check'
    DESCRIPTION = 'Looks at the files used by the app and their protection flags'

    ID          = 'file-protection'
    ISSUE_TITLE = 'Application Does Not Use Complete File Protection'
    FINDINGS    = 'The Team found the following files to have insecure protection flags:\n'

    def run(self):
        files = self.ANALYSIS.UTILS.run_on_ios('find {app} {data} -type f'.format(app=self.ANALYSIS.APP['Path'], data=self.ANALYSIS.IOS_DATA_PATH))[0].split('\r\n')
        vfiles = []
        for f in files:
            if f and not Utils.ignored_path(f) and not Utils.ignored_extension(f):
                protection = self.ANALYSIS.UTILS.dump_file_protect(f)
                if protection and 'NSFileProtectionComplete' not in protection:
                    vfiles += ['{file} ({prot})\n'.format(file=f, prot=protection.replace('\r\n', ''))]

        if vfiles:
            self.DETAILS = '* {details}'.format(details='* '.join(vfiles))
            self.REPORT  = True

