import datetime
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Any, Dict, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from prime_backup import constants
from prime_backup import logger
from prime_backup.config.config import Config
from prime_backup.types.backup_info import BackupInfo
from prime_backup.types.notification_event import NotificationEvent
from prime_backup.types.operator import Operator


class NotificationError(Exception):
	"""Base exception for notification errors"""
	pass


class NetworkError(NotificationError):
	"""Network-related errors (timeout, connection refused, etc.)"""
	pass


class ConfigError(NotificationError):
	"""Configuration errors (invalid URL, missing fields, etc.)"""
	pass


class DataError(NotificationError):
	"""Data serialization errors"""
	pass


def _get_plugin_version() -> str:
	try:
		from prime_backup.mcdr import mcdr_globals
		return mcdr_globals.metadata.version
	except Exception:
		try:
			from prime_backup.cli import cli_utils
			return cli_utils.get_plugin_version()
		except Exception:
			return '?'


def _get_server_running() -> Optional[bool]:
	try:
		from prime_backup.mcdr import mcdr_globals
		return mcdr_globals.server.is_server_running()
	except Exception:
		return None


def _get_translation(config: Config, key: str) -> str:
	"""
	Get translated text from language file.
	Fallback to English if translation not found.
	"""
	language = config.notification.language if hasattr(config, 'notification') else 'en_us'
	try:
		from ruamel.yaml import YAML
		import os
		from pathlib import Path
		
		# Get lang file path
		plugin_dir = Path(__file__).parent.parent.parent
		lang_file = plugin_dir / 'lang' / f'{language}.yml'
		
		if not lang_file.exists() and language != 'en_us':
			# Fallback to English
			lang_file = plugin_dir / 'lang' / 'en_us.yml'
		
		if lang_file.exists():
			yaml = YAML()
			with open(lang_file, 'r', encoding='utf-8') as f:
				data = yaml.load(f)
			
			# Navigate to the key
			keys = key.split('.')
			value = data
			for k in keys:
				if isinstance(value, dict) and k in value:
					value = value[k]
				else:
					return key  # Key not found, return the key itself
			return str(value)
	except Exception as e:
		logger.get().warning(f'Failed to get translation for {key}: {e}')
	return key


def _get_source_info(source: Optional[Any]) -> Optional[Dict[str, Any]]:
	if source is None:
		return None
	try:
		if getattr(source, 'is_player', False):
			return {
				'type': 'player',
				'name': source.player,
			}
		if getattr(source, 'is_console', False):
			return {
				'type': 'console',
				'name': '',
			}
		return {
			'type': 'command_source',
			'name': str(source),
		}
	except Exception:
		return {
			'type': 'unknown',
			'name': str(source),
		}


def _backup_to_payload(backup: BackupInfo) -> Dict[str, Any]:
	return {
		'id': backup.id,
		'date': backup.date_str,
		'comment': backup.comment,
		'creator': str(backup.creator),
		'targets': backup.targets,
		'tags': backup.tags.to_dict(),
		'file_count': backup.file_count,
		'raw_size': backup.raw_size,
		'stored_size': backup.stored_size,
	}


def _operator_to_payload(operator: Operator) -> Dict[str, Any]:
	return {
		'type': operator.type,
		'name': operator.name,
		'full': str(operator),
	}


def _make_payload(
		event: NotificationEvent, *,
		backup: Optional[BackupInfo],
		operator: Optional[Operator],
		source: Optional[Any],
		cost_s: Optional[float],
		message: Optional[str],
		error: Optional[Exception],
		extra: Optional[Dict[str, Any]],
		config: Config,
) -> Dict[str, Any]:
	now = time.time()
	version = str(_get_plugin_version())
	payload: Dict[str, Any] = {
		'event': event.value,
		'task': event.task,
		'status': event.status,
		'timestamp': {
			'unix': now,
			'iso': datetime.datetime.utcfromtimestamp(now).isoformat() + 'Z',
		},
		'plugin': {
			'id': constants.PLUGIN_ID,
			'version': version,
		},
		'server': {
			'running': _get_server_running(),
		},
	}

	if backup is not None:
		payload['backup'] = _backup_to_payload(backup)
	if operator is not None:
		payload['operator'] = _operator_to_payload(operator)
	if (src := _get_source_info(source)) is not None:
		payload['source'] = src
	if cost_s is not None:
		payload['cost_s'] = round(cost_s, 3)
	if message is not None:
		payload['message'] = message
	if error is not None:
		payload['error'] = {
			'type': error.__class__.__name__,
			'message': str(error),
		}
	if extra is not None:
		payload['extra'] = extra

	# Localized title
	title_template = _get_translation(config, 'prime_backup.notification.content.title')
	title = title_template.format(event.task, event.status)
	body_parts = [f'event={event.value}']
	if backup is not None:
		body_parts.append(f'backup=#{backup.id}')
	if message:
		body_parts.append(f'message={message}')
	payload['title'] = title
	payload['body'] = ', '.join(body_parts)
	payload['desp'] = payload['body']
	return payload


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_s: float):
	"""Post JSON data to URL with proper error handling"""
	try:
		data = json.dumps(payload, ensure_ascii=False).encode('utf8')
	except (TypeError, ValueError) as e:
		raise DataError(f'Failed to serialize payload: {e}') from e
	
	request_headers = {
		'Content-Type': 'application/json',
		'User-Agent': f'{constants.PLUGIN_ID}/{_get_plugin_version()}',
	}
	request_headers.update(headers)
	
	try:
		request = urllib.request.Request(url, data=data, headers=request_headers, method='POST')
		with urllib.request.urlopen(request, timeout=timeout_s) as response:
			response.read()
	except urllib.error.HTTPError as e:
		raise NetworkError(f'HTTP {e.code}: {e.reason}') from e
	except urllib.error.URLError as e:
		raise NetworkError(f'URL error: {e.reason}') from e
	except TimeoutError as e:
		raise NetworkError(f'Timeout after {timeout_s}s') from e
	except Exception as e:
		raise NetworkError(f'Request failed: {e}') from e


def _post_json_with_retry(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_s: float, retry_times: int) -> Tuple[bool, Optional[str]]:
	"""Post JSON with exponential backoff retry
	
	Returns:
		(success, error_message)
	"""
	last_error = None
	for attempt in range(retry_times + 1):
		try:
			_post_json(url, payload, headers, timeout_s)
			return True, None
		except NotificationError as e:
			last_error = str(e)
			if attempt < retry_times:
				# Exponential backoff: 1s, 2s, 4s
				delay = 2 ** attempt
				time.sleep(delay)
			continue
	
	return False, last_error


def _apply_if_not_none(data: Dict[str, Any], key: str, value: Any):
	if value is not None:
		data[key] = value


def _format_bark_body(base_payload: Dict[str, Any], *, markdown: bool, config: Config) -> str:
	backup = base_payload.get('backup') or {}
	operator = base_payload.get('operator') or {}
	source = base_payload.get('source') or {}
	error = base_payload.get('error') or {}

	def format_source() -> Optional[str]:
		src_type = source.get('type')
		if not src_type:
			return None
		src_name = source.get('name') or ''
		return f'{src_type}:{src_name}' if len(src_name) > 0 else src_type

	# Get localized field names
	def get_field_name(key: str) -> str:
		return _get_translation(config, f'prime_backup.notification.content.fields.{key}')

	fields = [
		(get_field_name('event'), base_payload.get('event')),
		(get_field_name('task'), base_payload.get('task')),
		(get_field_name('status'), base_payload.get('status')),
		(get_field_name('backup'), f"#{backup.get('id')}" if backup.get('id') is not None else None),
		(get_field_name('date'), backup.get('date')),
		(get_field_name('comment'), backup.get('comment')),
		(get_field_name('creator'), backup.get('creator')),
		(get_field_name('operator'), operator.get('full')),
		(get_field_name('source'), format_source()),
		(get_field_name('files'), (
			f"{backup.get('file_count')} files, raw={backup.get('raw_size')}, stored={backup.get('stored_size')}"
			if backup.get('file_count') is not None else None
		)),
		(get_field_name('cost'), f"{base_payload.get('cost_s')}s" if base_payload.get('cost_s') is not None else None),
		(get_field_name('message'), base_payload.get('message')),
		(get_field_name('error'), (
			f"{error.get('type')}: {error.get('message')}"
			if error.get('type') or error.get('message') else None
		)),
	]

	if markdown:
		lines = [f"- **{k}**: {v}" for k, v in fields if v not in [None, '']]
		return '\n'.join(lines)
	else:
		lines = [f"{k}: {v}" for k, v in fields if v not in [None, '']]
		return '\n'.join(lines)


def _resolve_bark_url(endpoint) -> str:
	url = endpoint.url
	device_key = getattr(endpoint.bark, 'device_key', None)
	if device_key:
		url = url.replace('{device_key}', device_key).replace('{key}', device_key)
	return url


def _make_bark_payload(base_payload: Dict[str, Any], endpoint, config: Config) -> Dict[str, Any]:
	bark = endpoint.bark
	markdown = bool(bark.markdown)
	default_body = _format_bark_body(base_payload, markdown=markdown, config=config)
	title = bark.title or base_payload.get('title')
	body = bark.body or default_body

	backup = base_payload.get('backup') or {}
	backup_id = backup.get('id')
	if title and backup_id is not None and f'#{backup_id}' not in title:
		title = f'{title} #{backup_id}'

	data: Dict[str, Any] = {}
	if markdown:
		data['markdown'] = body
	else:
		data['body'] = body
	_apply_if_not_none(data, 'title', title)
	_apply_if_not_none(data, 'subtitle', bark.subtitle)

	if bark.level is None:
		status = base_payload.get('status')
		if status == 'failure':
			data['level'] = 'critical'
		elif status == 'success':
			data['level'] = 'passive'
		else:
			data['level'] = 'active'
	else:
		data['level'] = bark.level
	_apply_if_not_none(data, 'volume', bark.volume)
	_apply_if_not_none(data, 'badge', bark.badge)
	_apply_if_not_none(data, 'call', bark.call)
	_apply_if_not_none(data, 'autoCopy', bark.autoCopy)
	_apply_if_not_none(data, 'copy', bark.copy)
	_apply_if_not_none(data, 'sound', bark.sound)
	_apply_if_not_none(data, 'icon', bark.icon)
	_apply_if_not_none(data, 'image', bark.image)
	_apply_if_not_none(data, 'group', bark.group or constants.PLUGIN_ID)
	_apply_if_not_none(data, 'url', bark.url)
	_apply_if_not_none(data, 'action', bark.action)
	_apply_if_not_none(data, 'id', bark.id)
	_apply_if_not_none(data, 'delete', bark.delete)
	_apply_if_not_none(data, 'isArchive', bark.isArchive)

	if bark.device_key and _resolve_bark_url(endpoint).rstrip('/').endswith('/push'):
		data['device_key'] = bark.device_key

	return data


def _send_to_endpoint(endpoint, payload: Dict[str, Any], config: Config) -> Tuple[str, bool, Optional[str], float]:
	"""Send notification to a single endpoint with retry
	
	Returns:
		(endpoint_name, success, error_message, duration_seconds)
	"""
	log = logger.get()
	start_time = time.time()
	
	if not endpoint.enabled:
		return (endpoint.name, False, 'Endpoint disabled', 0.0)
	
	if len(endpoint.url) == 0:
		log.warning('Notification endpoint {} has empty url, skipped'.format(endpoint.name))
		return (endpoint.name, False, 'Empty URL', 0.0)
	
	try:
		if endpoint.type == 'bark':
			bark_url = _resolve_bark_url(endpoint)
			bark_payload = _make_bark_payload(payload, endpoint, config)
			success, error_msg = _post_json_with_retry(
				bark_url, bark_payload, endpoint.headers, 
				endpoint.timeout.value, endpoint.retry_times
			)
		else:
			success, error_msg = _post_json_with_retry(
				endpoint.url, payload, endpoint.headers,
				endpoint.timeout.value, endpoint.retry_times
			)
		
		duration = time.time() - start_time
		if success:
			log.debug('Notification sent to {} in {:.2f}s'.format(endpoint.name, duration))
		else:
			log.warning('Failed to send notification to {} after retries: {}'.format(endpoint.name, error_msg))
		
		return (endpoint.name, success, error_msg, duration)
	
	except Exception as e:
		duration = time.time() - start_time
		error_msg = f'Unexpected error: {e}'
		log.error('Notification to {} failed with exception: {}'.format(endpoint.name, e))
		return (endpoint.name, False, error_msg, duration)


def notify(
		event: NotificationEvent, *,
		backup: Optional[BackupInfo] = None,
		operator: Optional[Operator] = None,
		source: Optional[Any] = None,
		cost_s: Optional[float] = None,
		message: Optional[str] = None,
		error: Optional[Exception] = None,
		extra: Optional[Dict[str, Any]] = None,
):
	"""Send notifications without tracking results (fire and forget)"""
	_ = notify_with_results(event, backup=backup, operator=operator, source=source, cost_s=cost_s, message=message, error=error, extra=extra)


def notify_with_results(
		event: NotificationEvent, *,
		backup: Optional[BackupInfo] = None,
		operator: Optional[Operator] = None,
		source: Optional[Any] = None,
		cost_s: Optional[float] = None,
		message: Optional[str] = None,
		error: Optional[Exception] = None,
		extra: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, bool, Optional[str], float]]:
	"""Send notifications and return detailed results for each endpoint (with concurrency)
	
	Returns:
		List of tuples: (endpoint_name, success, error_message, duration_seconds)
	"""
	config = Config.get().notification
	results = []
	
	if not config.enabled:
		return results
	if event not in config.events:
		return results
	if len(config.endpoints) == 0:
		return results

	payload = _make_payload(
		event,
		backup=backup,
		operator=operator,
		source=source,
		cost_s=cost_s,
		message=message,
		error=error,
		extra=extra,
		config=config,
	)

	# Send notifications concurrently to all enabled endpoints
	enabled_endpoints = [ep for ep in config.endpoints if ep.enabled]
	
	if len(enabled_endpoints) == 0:
		return results
	
	# Use ThreadPoolExecutor for concurrent sending
	max_workers = min(len(enabled_endpoints), 5)  # Limit to 5 concurrent requests
	with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='notify') as executor:
		# Submit all tasks
		future_to_endpoint = {
			executor.submit(_send_to_endpoint, endpoint, payload, config): endpoint
			for endpoint in enabled_endpoints
		}
		
		# Collect results as they complete
		for future in as_completed(future_to_endpoint):
			try:
				result = future.result()
				results.append(result)
			except Exception as e:
				endpoint = future_to_endpoint[future]
				logger.get().error('Unexpected error processing notification for {}: {}'.format(endpoint.name, e))
				results.append((endpoint.name, False, f'Processing error: {e}', 0.0))
	
	return results
