const API_BASE_URL = 'http://localhost:8000/api/v1';

const getAuthHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
});

export async function loginUser(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();
  return {
    token: data.access_token,
    user: {
      id: data.user.id,
      username: data.user.username,
      email: data.user.email,
      is_admin: data.user.is_admin,
    },
  };
}

export async function registerUser(username, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  const data = await response.json();
  // Auto-login after registration
  return loginUser(username, password);
}

export async function getEvents(limit = 50, skip = 0) {
  const response = await fetch(`${API_BASE_URL}/events?limit=${limit}&skip=${skip}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }

  return await response.json();
}

export async function deleteEvent(eventId) {
  const response = await fetch(`${API_BASE_URL}/events/${eventId}`, {
    method: 'DELETE',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete event');
  }
}

export async function createEvent(eventData) {
  const response = await fetch(`${API_BASE_URL}/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(eventData),
  });

  if (!response.ok) {
    throw new Error('Failed to create event');
  }

  return await response.json();
}

export async function getAnalytics(days = 7) {
  const response = await fetch(`${API_BASE_URL}/analytics/summary?days=${days}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch analytics');
  }

  return await response.json();
}

export async function getInsights(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/insights?limit=${limit}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch insights');
  }

  return await response.json();
}

export async function getHighConfidenceInsights(minConfidence = 0.8, limit = 50) {
  const response = await fetch(`${API_BASE_URL}/insights/high-confidence?min_confidence=${minConfidence}&limit=${limit}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch high-confidence insights');
  }

  return await response.json();
}

export async function getAnomalies(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/anomalies/alerts?limit=${limit}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch anomalies');
  }

  return await response.json();
}

export async function getAnomalySummary() {
  const response = await fetch(`${API_BASE_URL}/anomalies/summary`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch anomaly summary');
  }

  return await response.json();
}

export async function acknowledgeAnomaly(anomalyId) {
  const response = await fetch(`${API_BASE_URL}/anomalies/acknowledge/${anomalyId}`, {
    method: 'PATCH',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to acknowledge anomaly');
  }

  return await response.json();
}

export async function runAnomalyDetection(lookbackHours = 24) {
  const response = await fetch(`${API_BASE_URL}/anomalies/detect?lookback_hours=${lookbackHours}`, {
    method: 'POST',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to run anomaly detection');
  }

  return await response.json();
}

export async function getSavedViews() {
  const response = await fetch(`${API_BASE_URL}/saved-views`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch saved views');
  }

  return await response.json();
}

export async function createSavedView(viewData) {
  const response = await fetch(`${API_BASE_URL}/saved-views`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(viewData),
  });

  if (!response.ok) {
    throw new Error('Failed to create saved view');
  }

  return await response.json();
}

export async function updateSavedView(viewId, viewData) {
  const response = await fetch(`${API_BASE_URL}/saved-views/${viewId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(viewData),
  });

  if (!response.ok) {
    throw new Error('Failed to update saved view');
  }

  return await response.json();
}

export async function deleteSavedView(viewId) {
  const response = await fetch(`${API_BASE_URL}/saved-views/${viewId}`, {
    method: 'DELETE',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to delete saved view');
  }
}

export async function getAuditLogs(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/admin/audit-logs?limit=${limit}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch audit logs');
  }

  return await response.json();
}

export async function getUsers() {
  const response = await fetch(`${API_BASE_URL}/admin/users`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }

  return await response.json();
}

export async function createUser(userData) {
  const response = await fetch(`${API_BASE_URL}/admin/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create user');
  }

  return await response.json();
}

export async function setUserAdmin(userId, isAdmin) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/admin?is_admin=${isAdmin}`, {
    method: 'PATCH',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to update admin status');
  }

  return await response.json();
}

export async function activateUser(userId) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/activate`, {
    method: 'PATCH',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to activate user');
  }

  return await response.json();
}

export async function deactivateUser(userId) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/deactivate`, {
    method: 'PATCH',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to deactivate user');
  }

  return await response.json();
}

export async function deleteUser(userId) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to delete user');
  }

  return await response.json();
}
