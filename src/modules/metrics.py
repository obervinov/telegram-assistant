"""This module provides a way to expose metrics to Prometheus for monitoring the application."""
import time

from prometheus_client import start_http_server, Gauge
from logger import log


# pylint: disable=too-many-instance-attributes
class Metrics():
    """
    This class provides a way to expose metrics to Prometheus for monitoring the application.

    Attributes:
        :attribute port (int): port for the metrics server.
        :attribute interval (int): interval for collecting metrics.
        :attribute database (Database): instance of the Database class.
        :attribute running (bool): the status of the metrics server.
        :attribute access_granted_counter (Gauge): gauge for the access granted counter.
        :attribute access_denied_counter (Gauge): gauge for the access denied counter.

    Examples:
        >>> metrics = Metrics(port=8000, interval=1, metrics_prefix='pytest')
        >>> metrics.run(threads=[thread1, thread2])
        >>> metrics.stop()
    """
    def __init__(
        self,
        port: int = None,
        interval: int = None,
        metrics_prefix: str = None,
        **kwargs
    ) -> None:
        """
        The method initializes the class instance with the necessary parameters.

        Args:
            :param port (int): port for the metrics server.
            :param interval (int): interval for collecting metrics.
            :param metrics_prefix (str): prefix for the metrics.

        Keyword Args:
            :param database (Database): instance of the Database class.
        """
        metrics_prefix = metrics_prefix.replace('-', '_')

        self.port = port
        self.interval = interval
        self.database = kwargs.get('database', None)
        self.running = True
        self.thread_status_gauge = Gauge(f'{metrics_prefix}_thread_status', 'Thread status (1 = running, 0 = not running)', ['thread_name'])
        if self.database:
            self.access_granted_counter = Gauge(f'{metrics_prefix}_access_granted_total', 'Total number of users granted access')
            self.access_denied_counter = Gauge(f'{metrics_prefix}_access_denied_total', 'Total number of users denied access')

    def collect_users_stats(self) -> None:
        """
        The method collects information about users access status and updates the gauge.
        """
        users_dict = self.database.get_users(only_allowed=False)
        access_granted_count = 0
        access_denied_count = 0
        for user in users_dict:
            if user.get('status') == 'denied':
                access_denied_count += 1
            elif user.get('status') == 'allowed':
                access_granted_count += 1

        self.access_granted_counter.set(access_granted_count)
        self.access_denied_counter.set(access_denied_count)

    def update_thread_status(self, thread_name, is_running) -> None:
        """
        The method updates the gauge with the status of the thread.
        """
        self.thread_status_gauge.labels(thread_name).set(1 if is_running else 0)

    def run(self, threads: list) -> None:
        """
        The method starts the server and collects metrics.
        """
        start_http_server(self.port)
        log.info('[Metrics]: Metrics server started on port %s', self.port)
        while self.running:
            if self.database:
                self.collect_users_stats()
            for thread in threads:
                self.update_thread_status(thread.name, thread.is_alive())
            time.sleep(self.interval)

    def stop(self) -> None:
        """
        The method stops the metrics server.
        """
        self.running = False
        log.info('[Metrics]: Metrics server stopped')
