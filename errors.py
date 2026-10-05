"""User-facing diagnostics without exposing SDK payloads or credentials."""
class AnalysisValidationError(ValueError):
    pass

def explain_error(exc):
    if isinstance(exc, AnalysisValidationError):
        return str(exc)
    code = getattr(exc, 'code', None)
    if code in ('insufficient_quota', 'credit_balance_exhausted'):
        return 'The API reports no usable quota or credits. Check API Billing for the organization that owns this key.'
    if code in ('organization_spend_limit_exceeded', 'project_spend_limit_exceeded', 'organization_usage_limit_exceeded'):
        return 'An API spending or usage limit was reached. Check your organization and project limits.'
    name = type(exc).__name__
    messages = {
        'RateLimitError': 'The API rate limit was reached. Wait before retrying and check your model limits.',
        'AuthenticationError': 'The API key was rejected. Check the key in the sidebar.',
        'PermissionDeniedError': 'This API project does not have permission to use the selected model.',
        'NotFoundError': 'The selected model was not found or is not available to this API project.',
        'APITimeoutError': 'The API did not respond within the 3-minute network timeout. No automatic retry was sent. Wait briefly before trying again.',
        'ValidationError': 'The model response did not match the required analysis structure. Try running the analysis again.',
        'BadRequestError': 'The API rejected the model/request configuration. Check that the selected model supports structured Responses API output.',
    }
    return messages.get(name, f'The response could not be processed ({name}). Try again or use Demo Mode.')
