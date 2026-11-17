import http from './http'

export const authApi = {
  login: (payload) => http.post('/auth/login', payload),
  me: () => http.get('/auth/me'),
  logout: () => http.post('/auth/logout')
}

export const dashboardApi = {
  overview: () => http.get('/dashboard/overview')
}

export const projectApi = {
  list: (params) => http.get('/projects', { params }),
  options: () => http.get('/projects/options'),
  create: (payload) => http.post('/projects', payload),
  update: (id, payload) => http.put(`/projects/${id}`, payload),
  remove: (id) => http.delete(`/projects/${id}`)
}

export const sampleApi = {
  list: (params) => http.get('/samples', { params }),
  get: (id) => http.get(`/samples/${id}`),
  create: (payload) => http.post('/samples', payload),
  update: (id, payload) => http.put(`/samples/${id}`, payload),
  remove: (id) => http.delete(`/samples/${id}`)
}

export const recordApi = {
  list: (params) => http.get('/test-records', { params }),
  create: (payload) => http.post('/test-records', payload),
  update: (id, payload) => http.put(`/test-records/${id}`, payload),
  remove: (id) => http.delete(`/test-records/${id}`)
}

export const aiApi = {
  stats: () => http.get('/ai/stats'),
  grading: () => http.get('/ai/grading'),
  tasks: (params) => http.get('/ai/tasks', { params }),
  createTask: (payload) => http.post('/ai/tasks', payload),
  updateTask: (id, payload) => http.put(`/ai/tasks/${id}`, payload),
  removeTask: (id) => http.delete(`/ai/tasks/${id}`),
  defects: (params) => http.get('/ai/defects', { params }),
  createDefect: (payload) => http.post('/ai/defects', payload),
  updateDefect: (id, payload) => http.put(`/ai/defects/${id}`, payload),
  removeDefect: (id) => http.delete(`/ai/defects/${id}`)
}

export const userApi = {
  list: (params) => http.get('/users', { params }),
  create: (payload) => http.post('/users', payload),
  update: (id, payload) => http.patch(`/users/${id}`, payload)
}
