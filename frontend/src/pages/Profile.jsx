/* ==========================================
 * File: frontend/src/pages/Profile.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProfile } from '../api'
import './Profile.css'

const VACCINES = [
  { id: 'influenza',     name: 'Influenza (Flu)' },
  { id: 'dtap_ipv_hib',  name: 'DTaP-IPV-Hib' },
  { id: 'tdap_ipv',      name: 'Tdap-IPV' },
  { id: 'tdap',          name: 'Tdap' },
  { id: 'pneu_c_15',     name: 'Pneumococcal (Pneu-C-15)' },
  { id: 'pneu_c_20',     name: 'Pneumococcal (Pneu-C-20)' },
  { id: 'rotavirus',     name: 'Rotavirus' },
  { id: 'mmrv',          name: 'MMRV' },
  { id: 'mmr',           name: 'MMR' },
  { id: 'varicella',     name: 'Varicella (Chickenpox)' },
  { id: 'men_c_acyw',    name: 'Meningococcal (Men-C-ACYW)' },
  { id: 'hepatitis_b',   name: 'Hepatitis B' },
  { id: 'hepatitis_a',   name: 'Hepatitis A' },
  { id: 'hpv',           name: 'HPV' },
  { id: 'rsv',           name: 'RSV Vaccine' },
]

const RISK_FACTORS = [
  { key: 'is_pregnant',          label: 'Pregnant' },
  { key: 'is_immunocompromised', label: 'Immunocompromised' },
  { key: 'has_diabetes',         label: 'Diabetes' },
  { key: 'has_chronic_lung',     label: 'Chronic Lung Disease' },
  { key: 'has_heart_disease',    label: 'Chronic Heart Disease' },
  { key: 'has_chronic_kidney',   label: 'Chronic Kidney Disease' },
  { key: 'has_chronic_liver',    label: 'Chronic Liver Disease' },
  { key: 'has_asplenia',         label: 'Asplenia (No Spleen)' },
  { key: 'has_hiv',              label: 'HIV Positive' },
]

export default function Profile() {
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '', dob: '', gender: '',
    is_pregnant: false, is_immunocompromised: false,
    has_diabetes: false, has_chronic_lung: false,
    has_heart_disease: false, has_chronic_kidney: false,
    has_chronic_liver: false, has_asplenia: false, has_hiv: false,
  })

  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [step, setStep]       = useState(1)   // 1=personal, 2=risk, 3=history

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const addRow = () => setHistory(h => [...h, { vaccine_key: '', dose_number: 1, date_given: '' }])
  const removeRow = (i) => setHistory(h => h.filter((_, idx) => idx !== i))
  const updateRow = (i, key, val) => setHistory(h => h.map((r, idx) => idx === i ? { ...r, [key]: val } : r))

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const validHistory = history.filter(r => r.vaccine_key && r.date_given)
      await createProfile({ ...form, vaccination_history: validHistory })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile.')
      setStep(1)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile-page">
      <div className="profile-bg" />

      <div className="profile-container">
        <div className="profile-header fade-up">
          <div className="profile-step-label">New Patient Setup</div>
          <h1>Create Your Profile</h1>
          <p>We'll use this to calculate your vaccine eligibility based on Manitoba guidelines.</p>
        </div>

        {/* Step indicators */}
        <div className="step-bar fade-up">
          {['Personal Info', 'Risk Factors', 'Vaccine History'].map((s, i) => (
            <div key={i} className={`step-item ${step === i+1 ? 'active' : ''} ${step > i+1 ? 'done' : ''}`}>
              <div className="step-circle">{step > i+1 ? '✓' : i+1}</div>
              <span>{s}</span>
            </div>
          ))}
        </div>

        <div className="card profile-card fade-up">

          {/* STEP 1 — Personal Info */}
          {step === 1 && (
            <div className="step-content">
              <h2 className="step-title">Personal Information</h2>
              <div className="form-grid">
                <div className="form-group" style={{gridColumn: '1/-1'}}>
                  <label>Full Name *</label>
                  <input placeholder="John Smith" value={form.name} onChange={e => set('name', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Date of Birth *</label>
                  <input type="date" value={form.dob} onChange={e => set('dob', e.target.value)} max={new Date().toISOString().split('T')[0]} required />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select value={form.gender} onChange={e => set('gender', e.target.value)}>
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other / Prefer not to say</option>
                  </select>
                </div>
              </div>
              <div className="step-actions">
                <button className="btn btn-primary"
                  onClick={() => setStep(2)}
                  disabled={!form.name || !form.dob}>
                  Next: Risk Factors →
                </button>
              </div>
            </div>
          )}

          {/* STEP 2 — Risk Factors */}
          {step === 2 && (
            <div className="step-content">
              <h2 className="step-title">Medical History & Risk Factors</h2>
              <p className="step-desc">Check all conditions that apply. This helps determine which vaccines you're eligible for.</p>
              <div className="risk-grid">
                {RISK_FACTORS.map(rf => (
                  <label key={rf.key} className={`risk-item ${form[rf.key] ? 'checked' : ''}`}>
                    <input
                      type="checkbox"
                      checked={form[rf.key]}
                      onChange={e => set(rf.key, e.target.checked)}
                    />
                    <span className="risk-check">{form[rf.key] ? '✓' : ''}</span>
                    {rf.label}
                  </label>
                ))}
              </div>
              <div className="step-actions">
                <button className="btn btn-outline" onClick={() => setStep(1)}>← Back</button>
                <button className="btn btn-primary" onClick={() => setStep(3)}>Next: Vaccine History →</button>
              </div>
            </div>
          )}

          {/* STEP 3 — Vaccination History */}
          {step === 3 && (
            <div className="step-content">
              <h2 className="step-title">Vaccination History</h2>
              <p className="step-desc">Add any vaccines you've already received. Leave blank if you have no records — we'll mark everything as overdue.</p>

              {history.length === 0 && (
                <div className="empty-history">
                  No vaccination records added yet.
                </div>
              )}

              {history.map((row, i) => (
                <div key={i} className="history-row">
                  <div className="form-group">
                    <label>Vaccine</label>
                    <select value={row.vaccine_key} onChange={e => updateRow(i, 'vaccine_key', e.target.value)}>
                      <option value="">Select vaccine...</option>
                      {VACCINES.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Dose #</label>
                    <input type="number" min="1" max="4" value={row.dose_number}
                      onChange={e => updateRow(i, 'dose_number', parseInt(e.target.value))} />
                  </div>
                  <div className="form-group">
                    <label>Date Given</label>
                    <input type="date" value={row.date_given} max={new Date().toISOString().split('T')[0]}
                      onChange={e => updateRow(i, 'date_given', e.target.value)} />
                  </div>
                  <button className="btn btn-danger remove-btn" onClick={() => removeRow(i)}>✕</button>
                </div>
              ))}

              <button className="btn btn-outline add-btn" onClick={addRow}>+ Add Vaccine Record</button>

              {error && <div className="error-msg" style={{marginTop: 16}}>⚠ {error}</div>}

              <div className="step-actions">
                <button className="btn btn-outline" onClick={() => setStep(2)}>← Back</button>
                <button className="btn btn-primary" onClick={submit} disabled={loading}>
                  {loading ? <span className="spinner" /> : null}
                  Save & View Dashboard
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
