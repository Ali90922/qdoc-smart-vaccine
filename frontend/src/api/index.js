/* ==========================================
 * File: frontend/src/api/index.js
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import axios from 'axios'

const api = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

// Attach JWT token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth
export const signup  = (data) => api.post('/auth/signup', data)
export const login   = (data) => api.post('/auth/login', data)

// Profile
export const createProfile = (data) => api.post('/profile', data)
export const getProfile    = ()     => api.get('/profile/me')
export const updateProfile = (data) => api.put('/profile/me', data)
export const addVaccinationRecord = (data) => api.post('/profile/me/records', data)
export const deleteVaccinationRecord = (recordId) => api.delete(`/profile/me/records/${recordId}`)
export const updateVaccinationRecordDate = (recordId, data) => api.put(`/profile/me/records/${recordId}`, data)

// Dashboard
export const getDashboard  = ()     => api.get('/dashboard/me')

// Schedule
export const getSchedule   = ()     => api.get('/schedule/me')

// Reminders
export const sendReminder  = (data) => api.post('/reminders/send', data)
export const getReminders  = ()     => api.get('/reminders/me')

export default api
