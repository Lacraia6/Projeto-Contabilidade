"""Utility helpers for consistent API responses."""

from __future__ import annotations

from typing import Any, Dict, Optional


def success_response(
	data: Any = None,
	*,
	message: Optional[str] = None,
	pagination: Optional[Dict[str, Any]] = None,
	extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	"""Return a standardized success payload."""

	payload: Dict[str, Any] = {'success': True}
	if message:
		payload['message'] = message
	if data is not None:
		payload['data'] = data
	if pagination:
		payload['pagination'] = pagination
	if extra:
		payload.update(extra)
	return payload


def error_response(
	*,
	message: str,
	status_code: int,
	errors: Optional[Any] = None,
	extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	"""Return standardized error payload metadata (without Response object)."""

	payload: Dict[str, Any] = {
		'success': False,
		'message': message,
		'status_code': status_code,
	}
	if errors is not None:
		payload['errors'] = errors
	if extra:
		payload.update(extra)
	return payload
