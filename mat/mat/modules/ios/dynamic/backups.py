from mat.utils.utils import Utils, Issue

class Issue(Issue):

    TITLE       = 'File Backup Flag Check'
    DESCRIPTION = 'Looks at the files used by the app and their backup flag'

    ID          = 'permits-backups'
    ISSUE_TITLE = 'Application Permits Backups'
    FINDINGS    = 'The Team found the following files to have insecure backup flags:\n'

    def run(self):
        files = self.ANALYSIS.UTILS.run_on_ios('find {data}'.format(data=self.ANALYSIS.IOS_DATA_PATH))[0].split('\r\n')
        vfiles = []
        for f in files:
            if f and not Utils.ignored_path(f) and not Utils.ignored_extension(f):
                protection = self.ANALYSIS.UTILS.dump_backup_flag(f)
                if protection and '0' in protection:
                    vfiles += ['{file} ({prot})\n'.format(file=f, prot=protection.replace('\r\n', ''))]

        if vfiles:
            self.DETAILS = '* {details}'.format(details='* '.join(vfiles))
            self.REPORT  = True

