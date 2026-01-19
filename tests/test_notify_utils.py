import json
import unittest
from unittest.mock import patch, MagicMock

from prime_backup.config.notification_config import NotificationEndpoint, BarkOptions, NotificationConfig
from prime_backup.types.notification_event import NotificationEvent
from prime_backup.utils import notify_utils


class _DummyVersion:
	def __str__(self) -> str:
		return '1.2.3'


class NotifyUtilsTestCase(unittest.TestCase):
	def test_make_payload_version_json_serializable(self):
		from prime_backup.config.config import Config
		config = Config()
		config.notification = NotificationConfig()
		
		with patch('prime_backup.utils.notify_utils._get_plugin_version', return_value=_DummyVersion()):
			payload = notify_utils._make_payload(
				NotificationEvent.backup_start,
				backup=None,
				operator=None,
				source=None,
				cost_s=None,
				message=None,
				error=None,
				extra=None,
				config=config,
			)
			self.assertEqual('1.2.3', payload['plugin']['version'])
			json.dumps(payload, ensure_ascii=False)

	def test_bark_payload_support(self):
		from prime_backup.config.config import Config
		config = Config()
		config.notification = NotificationConfig()
		
		endpoint = NotificationEndpoint(
			type='bark',
			url='https://api.day.app/push',
			bark=BarkOptions(device_key='abc', group='pb', markdown=True),
		)
		base_payload = {
			'title': 'Prime Backup Notify backup success',
			'body': 'event=backup_success, backup=#1',
			'event': 'backup_success',
			'status': 'success',
			'task': 'backup',
			'backup': {
				'id': 1,
				'file_count': 10,
				'raw_size': 100,
				'stored_size': 80,
			},
		}
		bark_payload = notify_utils._make_bark_payload(base_payload, endpoint, config)
		self.assertIn('device_key', bark_payload)
		self.assertIn('markdown', bark_payload)
		self.assertNotIn('body', bark_payload)
		self.assertEqual('pb', bark_payload['group'])
		self.assertEqual('passive', bark_payload['level'])
		self.assertIn('backup', bark_payload['markdown'])

	def test_bark_url_placeholder(self):
		endpoint = NotificationEndpoint(
			type='bark',
			url='https://api.day.app/{device_key}',
			bark=BarkOptions(device_key='xyz'),
		)
		url = notify_utils._resolve_bark_url(endpoint)
		self.assertEqual('https://api.day.app/xyz', url)

	def test_bark_level_default_failure(self):
		from prime_backup.config.config import Config
		config = Config()
		config.notification = NotificationConfig()
		
		endpoint = NotificationEndpoint(type='bark', url='https://api.day.app/{device_key}', bark=BarkOptions(device_key='xyz'))
		base_payload = {
			'title': 'Prime Backup Notify backup failure',
			'event': 'backup_failure',
			'status': 'failure',
			'task': 'backup',
			'error': {
				'type': 'RuntimeError',
				'message': 'boom',
			},
		}
		bark_payload = notify_utils._make_bark_payload(base_payload, endpoint, config)
		self.assertEqual('critical', bark_payload['level'])

	def test_endpoint_url_validation(self):
		"""Test that empty URL raises error when endpoint is enabled"""
		with self.assertRaises(ValueError) as cm:
			endpoint = NotificationEndpoint(enabled=True, name='test', url='')
			endpoint.on_deserialization()
		self.assertIn('URL is empty', str(cm.exception))

	def test_endpoint_timeout_validation(self):
		"""Test that timeout validation works"""
		from prime_backup.types.units import Duration
		
		# Too short
		with self.assertRaises(ValueError) as cm:
			endpoint = NotificationEndpoint(url='http://example.com', timeout=Duration('0.5s'))
			endpoint.on_deserialization()
		self.assertIn('too short', str(cm.exception))
		
		# Too long
		with self.assertRaises(ValueError) as cm:
			endpoint = NotificationEndpoint(url='http://example.com', timeout=Duration('120s'))
			endpoint.on_deserialization()
		self.assertIn('too long', str(cm.exception))

	def test_endpoint_retry_validation(self):
		"""Test that retry_times validation works"""
		# Negative retry
		with self.assertRaises(ValueError) as cm:
			endpoint = NotificationEndpoint(url='http://example.com', retry_times=-1)
			endpoint.on_deserialization()
		self.assertIn('negative', str(cm.exception))
		
		# Too many retries
		with self.assertRaises(ValueError) as cm:
			endpoint = NotificationEndpoint(url='http://example.com', retry_times=10)
			endpoint.on_deserialization()
		self.assertIn('too large', str(cm.exception))

	def test_notification_errors(self):
		"""Test that custom exception types are raised correctly"""
		from prime_backup.utils.notify_utils import NetworkError, DataError
		
		# Test NetworkError on bad URL
		with self.assertRaises(NetworkError):
			notify_utils._post_json('http://invalid-url-that-does-not-exist-12345.com', {}, {}, 1)
		
		# Test DataError on non-serializable data (would be caught earlier in practice)
		# This is more of a demonstration of the error types

	def test_retry_mechanism(self):
		"""Test that retry mechanism works with exponential backoff"""
		call_count = 0
		
		def mock_post_fail(*args, **kwargs):
			nonlocal call_count
			call_count += 1
			raise notify_utils.NetworkError('Simulated failure')
		
		with patch('prime_backup.utils.notify_utils._post_json', side_effect=mock_post_fail):
			success, error = notify_utils._post_json_with_retry(
				'http://example.com', {}, {}, 1.0, retry_times=2
			)
			
			# Should have tried 3 times total (initial + 2 retries)
			self.assertEqual(call_count, 3)
			self.assertFalse(success)
			self.assertIsNotNone(error)

	def test_notify_with_results(self):
		"""Test notify_with_results returns proper result tuples"""
		from prime_backup.config.config import Config, set_config_instance
		
		# Create mock config
		config = Config()
		config.notification = NotificationConfig(
			enabled=True,
			events=[NotificationEvent.backup_success],
			endpoints=[
				NotificationEndpoint(
					enabled=True,
					name='test_endpoint',
					type='webhook',
					url='http://example.com/webhook'
				)
			]
		)
		set_config_instance(config)
		
		# Mock HTTP request
		with patch('prime_backup.utils.notify_utils._post_json') as mock_post:
			mock_post.return_value = None
			
			results = notify_utils.notify_with_results(NotificationEvent.backup_success)
			
			self.assertEqual(len(results), 1)
			endpoint_name, success, error_msg, duration = results[0]
			self.assertEqual(endpoint_name, 'test_endpoint')
			self.assertTrue(success)
			self.assertIsNone(error_msg)
			self.assertGreaterEqual(duration, 0)


if __name__ == '__main__':
	unittest.main()

