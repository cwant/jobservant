from jobservant.cluster_account import ClusterAccount


class TestClusterAccount:
    def test_log_level_info(self, capsys):
        cluster_account = ClusterAccount('some.cluster', log_level='info')
        cluster_account.log('info', 'I should be logged')
        cluster_account.log('debug', 'I should not be logged')

        captured = capsys.readouterr()
        assert captured.out == "INFO: I should be logged\n"

    def test_log_level_debug(self, capsys):
        cluster_account = ClusterAccount('some.cluster', log_level='debug')
        cluster_account.log('info', 'I should be logged')
        cluster_account.log('debug', 'I should also be logged')

        captured = capsys.readouterr()
        assert captured.out == ("INFO: I should be logged\n" +
                                "DEBUG: I should also be logged\n")

    def test_log_level_none(self, capsys):
        cluster_account = ClusterAccount('some.cluster', log_level='none')
        cluster_account.log('info', 'I should not be logged')
        cluster_account.log('debug', 'I should also not be logged')

        captured = capsys.readouterr()
        assert captured.out == ""
