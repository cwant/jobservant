class HasALogger:
    def init_logging(self, **kwargs):
        self.log_level = kwargs.get('log_level', 'info')
        if self.log_level not in ['none', 'info', 'debug']:
            raise ValueError('Bad log_level')

    def log(self, level, message):
        if self.log_level == 'none':
            return
        if self.log_level == 'info' and level == 'debug':
            return
        self.write_to_log(level, message)

    # Override this one for more meaningful logging
    def write_to_log(self, level, message):
        print('%s: %s' % (level.upper(), message))
