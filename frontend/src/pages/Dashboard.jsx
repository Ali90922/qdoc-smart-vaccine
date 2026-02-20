/* ==========================================
 * File: frontend/src/pages/Dashboard.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import QdocLegacySection from '../components/QdocLegacySection'
import { getDashboard, sendReminder } from '../api'
import './Dashboard.css'

const STATUS_CONFIG = {
  OVERDUE:     { label: 'Overdue',     cls: 'overdue',      icon: '⚠' },
  DUE_SOON:    { label: 'Due Soon',    cls: 'due_soon',     icon: '⏰' },
  UP_TO_DATE:  { label: 'Up to Date',  cls: 'up_to_date',   icon: '✓' },
  NOT_ELIGIBLE:{ label: 'Not Eligible',cls: 'not_eligible', icon: '—' },
}

function Badge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOT_ELIGIBLE
  return <span className={`badge badge-${cfg.cls}`}>{cfg.icon} {cfg.label}</span>
}

function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-CA', { year:'numeric', month:'short', day:'numeric' })
}

function tooltipText(v) {
  const lines = [
    `Status: ${STATUS_CONFIG[v.status]?.label || v.status}`,
    `Doses: ${v.doses_received}/${v.doses_required}`,
    `Last Dose: ${fmtDate(v.last_dose)}`,
    `Next Due: ${v.next_due ? fmtDate(v.next_due) : '—'}`,
  ]
  if (v.reason) lines.unshift(`Reason: ${v.reason}`)
  return lines.join('\n')
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [filter, setFilter]     = useState('ALL')
  const [sending, setSending]   = useState({})
  const [toast, setToast]       = useState('')
  const [reminderModal, setReminderModal] = useState(null)

  useEffect(() => {
    getDashboard()
      .then(r => setData(r.data))
      .catch(err => {
        if (err.response?.status === 404) navigate('/profile')
        else setError('Failed to load dashboard.')
      })
      .finally(() => setLoading(false))
  }, [])

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  const handleRemind = async (type, vaccine_key, vaccine_name) => {
    setSending(s => ({ ...s, [vaccine_key]: true }))
    try {
      await sendReminder({ vaccine_key, reminder_type: type })
      setReminderModal(null)
      showToast(`🔔 Reminder set for ${vaccine_name}`)
    } catch {
      showToast('Failed to send reminder.')
    } finally {
      setSending(s => ({ ...s, [vaccine_key]: false }))
    }
  }

  if (loading) return (
    <div className="page-loading">
      <div className="spinner" style={{width:36,height:36,borderWidth:3}} />
      <p>Loading your vaccine status...</p>
    </div>
  )

  if (error) return (
    <div className="page-loading">
      <p className="error-msg">{error}</p>
    </div>
  )

  const vaccines = data?.vaccines || []
  const summary  = data?.summary  || {}

  const filtered = filter === 'ALL'
    ? vaccines
    : vaccines.filter(v => v.status === filter)

  return (
    <>
      <div className="dashboard-page">
        <Navbar />

        {toast && <div className="toast fade-in">{toast}</div>}

        {reminderModal && (
          <div className="modal-overlay" onClick={() => setReminderModal(null)}>
            <div className="modal card" onClick={e => e.stopPropagation()}>
              <h3 className="modal-title">Set Reminder</h3>
              <p className="modal-sub">How would you like to be reminded about <strong>{reminderModal.name}</strong>?</p>
              <div className="modal-options">
                <button className="remind-opt" onClick={() => handleRemind('email', reminderModal.key, reminderModal.name)}>
                  <span className="remind-icon">📧</span>
                  <span className="remind-label">Email</span>
                  <span className="remind-desc">Send to your registered email</span>
                </button>
                <button className="remind-opt" onClick={() => handleRemind('sms', reminderModal.key, reminderModal.name)}>
                  <span className="remind-icon">📱</span>
                  <span className="remind-label">SMS</span>
                  <span className="remind-desc">Text message reminder</span>
                </button>
                <button className="remind-opt" onClick={() => handleRemind('in_app', reminderModal.key, reminderModal.name)}>
                  <span className="remind-icon">🔔</span>
                  <span className="remind-label">In-App</span>
                  <span className="remind-desc">Notification in the app</span>
                </button>
              </div>
              <button className="btn btn-outline" style={{width:'100%', justifyContent:'center'}} onClick={() => setReminderModal(null)}>Cancel</button>
            </div>
          </div>
        )}

        <div className="dashboard-container">
          {/* Header */}
          <div className="dash-header fade-up">
            <div>
              <p className="dash-welcome">Welcome back</p>
              <h1 className="dash-name">{data?.patient_name}</h1>
            </div>
            <p className="dash-date">{new Date().toLocaleDateString('en-CA', { weekday:'long', year:'numeric', month:'long', day:'numeric' })}</p>
          </div>

          {/* Summary cards */}
          <div className="summary-grid fade-up">
            <div className="summary-card overdue-card">
              <div className="summary-num">{summary.overdue || 0}</div>
              <div className="summary-label">Overdue</div>
              <div className="summary-icon">⚠</div>
            </div>
            <div className="summary-card duesoon-card">
              <div className="summary-num">{summary.due_soon || 0}</div>
              <div className="summary-label">Due Soon</div>
              <div className="summary-icon">⏰</div>
            </div>
            <div className="summary-card uptodate-card">
              <div className="summary-num">{summary.up_to_date || 0}</div>
              <div className="summary-label">Up to Date</div>
              <div className="summary-icon">✓</div>
            </div>
            <div className="summary-card noteligible-card">
              <div className="summary-num">{summary.not_eligible || 0}</div>
              <div className="summary-label">Not Eligible</div>
              <div className="summary-icon">—</div>
            </div>
          </div>

          {/* Filter bar */}
          <div className="filter-bar fade-up">
            <span className="filter-label">Filter:</span>
            {['ALL','OVERDUE','DUE_SOON','UP_TO_DATE','NOT_ELIGIBLE'].map(f => (
              <button key={f} className={`filter-btn ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
                {f === 'ALL' ? 'All' : STATUS_CONFIG[f]?.label}
              </button>
            ))}
          </div>

          {/* Vaccine table */}
          <div className="card vaccine-table fade-up">
            <div className="table-header">
              <span>Vaccine</span>
              <span>Status</span>
              <span>Last Dose</span>
              <span>Next Due</span>
              <span>Doses</span>
              <span>Action</span>
            </div>

            {filtered.length === 0 && (
              <div className="table-empty">No vaccines match this filter.</div>
            )}

            {filtered.map((v, i) => (
              <div key={v.vaccine_key} className={`table-row ${v.status.toLowerCase()}`} style={{ animationDelay: `${i * 0.04}s` }}>
                <div className="vaccine-name has-tooltip" tabIndex={0} aria-label={tooltipText(v)}>
                  <span className="vname">{v.vaccine_name} <span className="vname-info">ⓘ</span></span>
                  {v.reason && <span className="vreason">{v.reason}</span>}
                  <span className="vtooltip" role="tooltip">
                    <strong>{v.vaccine_name}</strong>
                    <span>{`Status: ${STATUS_CONFIG[v.status]?.label || v.status}`}</span>
                    {v.reason && <span>{`Reason: ${v.reason}`}</span>}
                    <span>{`Doses: ${v.doses_received}/${v.doses_required}`}</span>
                    <span>{`Last Dose: ${fmtDate(v.last_dose)}`}</span>
                    <span>{`Next Due: ${v.next_due ? fmtDate(v.next_due) : '—'}`}</span>
                  </span>
                </div>
                <div><Badge status={v.status} /></div>
                <div className="date-cell">{fmtDate(v.last_dose)}</div>
                <div className="date-cell">
                  {v.next_due ? fmtDate(v.next_due) : '—'}
                  {v.days_until != null && <span className="days-tag">{v.days_until}d</span>}
                </div>
                <div className="dose-cell">{v.doses_received}/{v.doses_required}</div>
                <div>
                  {(v.status === 'OVERDUE' || v.status === 'DUE_SOON') && (
                    <button
                      className="btn btn-remind"
                      onClick={() => setReminderModal({ key: v.vaccine_key, name: v.vaccine_name })}
                      disabled={sending[v.vaccine_key]}
                    >
                      {sending[v.vaccine_key] ? <span className="spinner" style={{width:14,height:14}} /> : '🔔 Remind'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <QdocLegacySection />
    </>
  )
}
