/* ==========================================
 * File: frontend/src/pages/Schedule.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { getSchedule } from '../api'
import './Schedule.css'

function parseDateLocal(d) {
  if (!d) return null
  const s = String(d)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  const dt = new Date(s)
  if (Number.isNaN(dt.getTime())) return null
  return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate())
}

function fmtDate(d) {
  if (!d) return '—'
  const dt = parseDateLocal(d)
  if (!dt) return '—'
  return dt.toLocaleDateString('en-CA', { year: 'numeric', month: 'long', day: 'numeric' })
}

function fmtMonth(d) {
  const dt = parseDateLocal(d)
  if (!dt) return '—'
  return dt.toLocaleDateString('en-CA', { month: 'short' }).toUpperCase()
}

function fmtDay(d) {
  const dt = parseDateLocal(d)
  if (!dt) return '—'
  return dt.getDate()
}

function coverageHint(daysUntil) {
  if (daysUntil == null) return 'Coverage window active'
  if (daysUntil < 0) return `Coverage ended ${Math.abs(daysUntil)} days ago`
  if (daysUntil === 0) return 'Coverage ends today'
  return `Coverage remains for ${daysUntil} day${daysUntil === 1 ? '' : 's'}`
}

export default function Schedule() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')

  useEffect(() => {
    getSchedule()
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load schedule.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div><Navbar /><div className="page-loading"><div className="spinner" style={{width:36,height:36,borderWidth:3}}/><p>Loading schedule...</p></div></div>
  )

  const upcoming = data?.upcoming || []
  const dueSoon  = upcoming.filter(v => v.status === 'DUE_SOON')
  const future   = upcoming.filter(v => v.status === 'UP_TO_DATE')

  return (
    <div className="schedule-page">
      <Navbar />
      <div className="schedule-container">

        <div className="sched-header fade-up">
          <h1>Upcoming Schedule</h1>
          <p>Your upcoming vaccine appointments based on Manitoba immunization guidelines.</p>
        </div>

        {error && <div className="error-msg">{error}</div>}

        {upcoming.length === 0 && !error && (
          <div className="card sched-empty fade-up">
            <div className="empty-icon">OK</div>
            <h3>You're all caught up!</h3>
            <p>No upcoming vaccines found. Check your dashboard for overdue vaccines.</p>
          </div>
        )}

        {/* Due Soon section */}
        {dueSoon.length > 0 && (
          <div className="fade-up">
            <div className="section-label">Action Required - Due Within 30 Days</div>
            <div className="sched-grid">
              {dueSoon.map((v, i) => (
                <div key={v.vaccine_key} className="sched-card due-soon-card" style={{animationDelay:`${i*0.06}s`}}>
                  <div className="sched-date-box warn">
                    <div className="sched-month">{fmtMonth(v.due_date)}</div>
                    <div className="sched-day">{fmtDay(v.due_date)}</div>
                  </div>
                  <div className="sched-info">
                    <div className="sched-vname">{v.vaccine_name}</div>
                    <div className="sched-due">Due {fmtDate(v.due_date)}</div>
                    <div className="sched-coverage">{coverageHint(v.days_until)}</div>
                  </div>
                  <div className="sched-badge warn-badge">
                    {v.days_until === 0 ? 'Today' : `${v.days_until}d left`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Future section */}
        {future.length > 0 && (
          <div className="fade-up" style={{marginTop: 36}}>
            <div className="section-label">Scheduled - Future Doses</div>
            <div className="timeline-list">
              {future.map((v, i) => (
                <div key={v.vaccine_key} className="timeline-item" style={{animationDelay:`${i*0.05}s`}}>
                  <div className="timeline-dot" />
                  <div className="timeline-date-box">
                    <div className="tl-month">{fmtMonth(v.due_date)}</div>
                    <div className="tl-day">{fmtDay(v.due_date)}</div>
                    <div className="tl-year">{parseDateLocal(v.due_date)?.getFullYear() || '—'}</div>
                  </div>
                  <div className="timeline-content card">
                    <div className="tl-vname">{v.vaccine_name}</div>
                    <div className="tl-vdate">Due {fmtDate(v.due_date)}</div>
                    <div className="tl-coverage">{coverageHint(v.days_until)}</div>
                    {v.days_until != null && (
                      <div className="tl-days">in {v.days_until} days</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
