from IPython.display import HTML, display


class JobStatusTable:

    def __init__(self, cluster_job, **kwargs):
        self.cluster_job = cluster_job
        self.is_table_style_set = False

    def run(self, *kwargs):
        data = [['Cluster', self.cluster_job.cluster_account.server],
                ['Username', self.cluster_job.cluster_account.username],
                ['Job ID', self.cluster_job.jobid]]

        queue_status = self.cluster_job.queue_status_hash()
        if queue_status == {}:
            data += [['State', 'Finished']]
        else:
            data += [['State', queue_status['STATE']],
                     ['Accounting group', queue_status['ACCOUNT']],
                     ['Partition', queue_status['PARTITION']]]
        self.render_vertical_table(data)

    def render_vertical_table(self, data_table):
        self.setup_table_style()

        # Each row in data_table has header, data, (optional) class
        html = '<table>'
        for row in data_table:
            class_string = ''
            if len(row) > 2:
                class_string = ' class={}'.format(row[2])
            header = '<th>{}</th>'.format(row[0])
            data = '<td>{}</t1>'.format(row[1])
            html += '<tr{}>{}{}</tr>'.format(class_string,
                                             header,
                                             data)
        html += '</table>'
        display(HTML(html))

    def setup_table_style(self):
        if self.is_table_style_set:
            return
        display(HTML("""
        <style>
        .rendered_html td {
          text-align: left;
        }
        </style>
        """))
        self.is_table_style_set = True
