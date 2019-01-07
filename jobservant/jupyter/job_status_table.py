from IPython.display import HTML, display


class JobStatusTable:

    def __init__(self, cluster_job, **kwargs):
        self.cluster_job = cluster_job
        self.html = None
        self.should_separate_next_line = None
        self.is_table_style_set = False
        self.section_class = None

    def run(self, *kwargs):
        self.start_table()
        self.add_row('Cluster',
                     self.cluster_job.cluster_account.server)
        self.add_row('Username',
                     self.cluster_job.cluster_account.username)
        self.add_row('Job ID', self.cluster_job.jobid)

        self.add_separator(section_class='job-status')
        queue_status = self.cluster_job.queue_status_hash()
        if queue_status == {}:
            self.add_row('State', 'Finished')
        else:
            self.add_row('State', queue_status['STATE'])

            self.add_separator()
            self.add_row('Accounting group', queue_status['ACCOUNT'])
            self.add_row('Partition', queue_status['PARTITION'])

            self.add_separator()
            self.add_row('Submit time', queue_status['SUBMIT_TIME'])
            self.add_row('Start time', queue_status['START_TIME'])
            self.add_row('End time', queue_status['END_TIME'])

            self.add_separator()
            self.add_row('Node list', queue_status['NODELIST'])

        self.finish_table()

    def start_table(self):
        self.setup_table_style()

        self.html = '<table class="jobservant status-table">'
        self.should_separate_next_line = False
        self.section_class = None

    def finish_table(self):
        self.html += '</table>'
        display(HTML(self.html))

    def add_separator(self, **kwargs):
        self.should_separate_next_line = True
        self.section_class = kwargs.get('section_class')

    def add_row(self, heading, data, **kwargs):
        class_string = kwargs.get('class', '')
        if self.should_separate_next_line:
            class_string += ' line-above'
            self.should_separate_next_line = False
        if self.section_class:
            class_string += ' {}'.format(self.section_class)
        if len(class_string) > 0:
            class_string = ' class="{}"'.format(class_string)
        row = '<th>{}</th>'.format(heading) + \
            '<td>{}</td>'.format(data)
        self.html += '<tr{}>{}</tr>'.format(class_string, row)

    def setup_table_style(self):
        if self.is_table_style_set:
            return
        display(HTML("""
        <style>
          .rendered_html th {
            border-right: solid 1px #888;
          }
          .rendered_html td {
            text-align: left;
          }
          .rendered_html tr.line-above {
            border-top: 1px solid #888;
          }
          .rendered_html tbody tr:nth-child(odd):not(:hover) {
            background: inherit;
          }
          .rendered_html tbody tr.job-status:not(:hover) {
            background: #eeeeff;
          }
        </style>
        """))
        self.is_table_style_set = True
