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
  OVERDUE:     { label: 'Overdue',     cls: 'overdue',      icon: '!' },
  DUE_SOON:    { label: 'Due Soon',    cls: 'due_soon',     icon: 'TIME' },
  UP_TO_DATE:  { label: 'Up to Date',  cls: 'up_to_date',   icon: 'OK' },
  NOT_ELIGIBLE:{ label: 'Not Eligible',cls: 'not_eligible', icon: '-' },
}

const VACCINE_INFO = {
  influenza: 'Annual seasonal flu vaccine recommended for people 6 months and older.',
  dtap_ipv_hib: 'Childhood combo vaccine for diphtheria, tetanus, pertussis, polio, and Hib.',
  tdap_ipv: 'Preschool booster covering tetanus, diphtheria, pertussis, and polio.',
  tdap: 'Booster for adolescents/adults to maintain protection against tetanus, diphtheria, and pertussis.',
  pneu_c_15: 'Pneumococcal vaccine typically used in infant immunization schedules.',
  pneu_c_20: 'Pneumococcal vaccine for eligible adults, including seniors and high-risk patients.',
  rotavirus: 'Infant vaccine that helps prevent severe rotavirus diarrhea and dehydration.',
  mmrv: 'Combined measles, mumps, rubella, and varicella vaccine for pediatric use.',
  mmr: 'Measles, mumps, rubella vaccine commonly used in older children and adults.',
  varicella: 'Chickenpox protection vaccine, often delivered in a 2-dose series.',
  men_c_acyw: 'Meningococcal vaccine that protects against multiple invasive strains.',
  hepatitis_b: 'Hepatitis B protection, often delivered as a multi-dose series.',
  hepatitis_a: 'Hepatitis A vaccine for eligible groups, including certain higher-risk patients.',
  hpv: 'Human papillomavirus vaccine that lowers risk of HPV-related cancers.',
  rsv: 'Respiratory syncytial virus protection for eligible older adults.',
}

function Badge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOT_ELIGIBLE
  return <span className={`badge badge-${cfg.cls}`}>{cfg.icon} {cfg.label}</span>
}

function fmtDate(d) {
  if (!d) return '—'
  const dt = parseDateLocal(d)
  if (!dt) return '—'
  return dt.toLocaleDateString('en-CA', { year:'numeric', month:'short', day:'numeric' })
}

function getNextDueDisplay(v) {
  if (v?.status === 'OVERDUE') return fmtDate(new Date())
  if (v?.next_due) return fmtDate(v.next_due)
  return '—'
}

function parseDateLocal(d) {
  if (!d) return null
  const s = String(d)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  const dt = new Date(s)
  if (Number.isNaN(dt.getTime())) return null
  return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate())
}

function dayDiffFromToday(d) {
  if (!d) return null
  const msPerDay = 24 * 60 * 60 * 1000
  const today = new Date()
  const now = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()
  const target = parseDateLocal(d)
  if (!target) return null
  const end = target.getTime()
  return Math.floor((end - now) / msPerDay)
}

function getProtectionMeta(v) {
  if (!v.last_dose && (v.doses_received || 0) === 0) {
    return { cls: 'none', label: 'No active protection', detail: 'No dose recorded yet' }
  }

  if (v.next_due) {
    const days = v.days_until != null ? v.days_until : dayDiffFromToday(v.next_due)
    if (days < 0) {
      return {
        cls: 'expired',
        label: `Expired ${Math.abs(days)}d ago`,
        detail: `Coverage ended ${fmtDate(v.next_due)}`
      }
    }
    if (days === 0) {
      return { cls: 'warning', label: 'Ends today', detail: `Coverage ends ${fmtDate(v.next_due)}` }
    }
    if (days <= 30) {
      return {
        cls: 'warning',
        label: `${days}d remaining`,
        detail: `Coverage ends ${fmtDate(v.next_due)}`
      }
    }
    return {
      cls: 'active',
      label: `${days}d protected`,
      detail: `Coverage until ${fmtDate(v.next_due)}`
    }
  }

  if ((v.doses_received || 0) >= (v.doses_required || 0)) {
    return { cls: 'complete', label: 'Series complete', detail: 'No routine expiry configured' }
  }

  return { cls: 'building', label: 'Partial protection', detail: 'Further dose(s) required' }
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
  const [expandedKey, setExpandedKey] = useState(null)

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
      showToast(`Reminder set for ${vaccine_name}`)
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
                  <span className="remind-icon">EMAIL</span>
                  <span className="remind-label">Email</span>
                  <span className="remind-desc">Send to your registered email</span>
                </button>
                <button className="remind-opt" onClick={() => handleRemind('sms', reminderModal.key, reminderModal.name)}>
                  <span className="remind-icon">SMS</span>
                  <span className="remind-label">SMS</span>
                  <span className="remind-desc">Text message reminder</span>
                </button>
                <button className="remind-opt" onClick={() => handleRemind('in_app', reminderModal.key, reminderModal.name)}>
                  <span className="remind-icon">APP</span>
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
              <div className="summary-icon">!</div>
            </div>
            <div className="summary-card duesoon-card">
              <div className="summary-num">{summary.due_soon || 0}</div>
              <div className="summary-label">Due Soon</div>
              <div className="summary-icon">TIME</div>
            </div>
            <div className="summary-card uptodate-card">
              <div className="summary-num">{summary.up_to_date || 0}</div>
              <div className="summary-label">Up to Date</div>
              <div className="summary-icon">OK</div>
            </div>
            <div className="summary-card noteligible-card">
              <div className="summary-num">{summary.not_eligible || 0}</div>
              <div className="summary-label">Not Eligible</div>
              <div className="summary-icon">-</div>
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
              <span>Protection</span>
              <span>Doses</span>
              <span>Action</span>
            </div>

            {filtered.length === 0 && (
              <div className="table-empty">No vaccines match this filter.</div>
            )}

            {filtered.map((v, i) => {
              const isExpanded = expandedKey === v.vaccine_key
              const protection = getProtectionMeta(v)
              return (
                <div key={v.vaccine_key}>
                  <div className={`table-row ${v.status.toLowerCase()}`} style={{ animationDelay: `${i * 0.04}s` }}>
                    <div className="vaccine-name">
                      <button
                        className="vname-toggle"
                        onClick={() => setExpandedKey(isExpanded ? null : v.vaccine_key)}
                        aria-expanded={isExpanded}
                      >
                        <span className="vname">{v.vaccine_name}</span>
                        <span className="vname-info">{isExpanded ? '▴' : '▾'}</span>
                      </button>
                      {v.reason && <span className="vreason">{v.reason}</span>}
                    </div>
                    <div><Badge status={v.status} /></div>
                    <div className="date-cell">{fmtDate(v.last_dose)}</div>
                    <div className="date-cell">
                      {getNextDueDisplay(v)}
                      {v.days_until != null && v.status !== 'OVERDUE' && <span className="days-tag">{v.days_until}d</span>}
                    </div>
                    <div className="protect-cell">
                      <span className={`protect-pill ${protection.cls}`}>{protection.label}</span>
                      <span className="protect-note">{protection.detail}</span>
                    </div>
                    <div className="dose-cell">{v.doses_received}/{v.doses_required}</div>
                    <div>
                      {(v.status === 'OVERDUE' || v.status === 'DUE_SOON') && (
                        <button
                          className="btn btn-remind"
                          onClick={() => setReminderModal({ key: v.vaccine_key, name: v.vaccine_name })}
                          disabled={sending[v.vaccine_key]}
                        >
                          {sending[v.vaccine_key] ? <span className="spinner" style={{width:14,height:14}} /> : 'Remind'}
                        </button>
                      )}
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="table-row-expanded">
                      <div className="expanded-grid">
                        <p><strong>Status:</strong> {STATUS_CONFIG[v.status]?.label || v.status}</p>
                        <p><strong>Protection:</strong> {protection.label} ({protection.detail})</p>
                        <p><strong>Dose Progress:</strong> {v.doses_received}/{v.doses_required}</p>
                        <p><strong>Last Dose:</strong> {fmtDate(v.last_dose)}</p>
                        <p><strong>Next Due:</strong> {getNextDueDisplay(v)}</p>
                        {v.reason && <p><strong>Reason:</strong> {v.reason}</p>}
                        <p><strong>About this vaccine:</strong> {VACCINE_INFO[v.vaccine_key] || 'General protection vaccine included in your schedule based on age/risk rules.'}</p>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
      <QdocLegacySection />
    </>
  )
}
