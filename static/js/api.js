export const API_BASE = '/api/v1/'
export const HOST_PORT = window.location.port === 80 ? '' : `:${window.location.port}`
export const HOST_URL = `${window.location.protocol}//${window.location.hostname}${HOST_PORT}`
