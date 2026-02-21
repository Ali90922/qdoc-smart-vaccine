/* ==========================================
 * File: frontend/src/pages/Profile.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import {
  addVaccinationRecord,
  createProfile,
  deleteVaccinationRecord,
  getProfile,
  updateProfile,
  updateVaccinationRecordDate,
} from '../api'
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
  return dt.toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' })
}

function inferDoseHistory(rows) {
  const grouped = new Map()
  for (const row of rows) {
    if (!row.vaccine_key || !row.date_given) continue
    if (!grouped.has(row.vaccine_key)) grouped.set(row.vaccine_key, [])
    grouped.get(row.vaccine_key).push(row)
  }

  const inferred = []
  for (const [vaccineKey, entries] of grouped.entries()) {
    const ordered = [...entries].sort(
      (a, b) => (parseDateLocal(a.date_given)?.getTime() || 0) - (parseDateLocal(b.date_given)?.getTime() || 0)
    )
    ordered.forEach((entry, idx) => {
      inferred.push({
        vaccine_key: vaccineKey,
        dose_number: idx + 1,
        date_given: entry.date_given,
      })
    })
  }
  return inferred
}

export default function Profile() {
  const navigate = useNavigate()

  const [existingProfile, setExistingProfile] = useState(null)
  const [loadingProfile, setLoadingProfile] = useState(true)

  const [form, setForm] = useState({
    name: '', dob: '', gender: '',
    is_pregnant: false, is_immunocompromised: false,
    has_diabetes: false, has_chronic_lung: false,
    has_heart_disease: false, has_chronic_kidney: false,
    has_chronic_liver: false, has_asplenia: false, has_hiv: false,
  })

  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState(1)
  const [addRecordForm, setAddRecordForm] = useState({ vaccine_key: '', date_given: '' })
  const [addingRecord, setAddingRecord] = useState(false)
  const [addRecordError, setAddRecordError] = useState('')
  const [addRecordSuccess, setAddRecordSuccess] = useState('')
  const [deletingRecordId, setDeletingRecordId] = useState(null)
  const [editingDateId, setEditingDateId] = useState(null)
  const [editingDateValue, setEditingDateValue] = useState('')
  const [updatingDateId, setUpdatingDateId] = useState(null)
  const [editingRisks, setEditingRisks] = useState(false)
  const [savingRisks, setSavingRisks] = useState(false)
  const [riskError, setRiskError] = useState('')
  const [riskSuccess, setRiskSuccess] = useState('')
  const [riskForm, setRiskForm] = useState({
    gender: '',
    is_pregnant: false,
    is_immunocompromised: false,
    has_diabetes: false,
    has_chronic_lung: false,
    has_heart_disease: false,
    has_chronic_kidney: false,
    has_chronic_liver: false,
    has_asplenia: false,
    has_hiv: false,
  })

  useEffect(() => {
    getProfile()
      .then((r) => setExistingProfile(r.data))
      .catch((err) => {
        if (err.response?.status !== 404) {
          setError('Failed to load profile.')
        }
      })
      .finally(() => setLoadingProfile(false))
  }, [])

  const selectedRisks = useMemo(() => {
    if (!existingProfile) return []
    return RISK_FACTORS.filter((rf) => existingProfile[rf.key]).map((rf) => rf.label)
  }, [existingProfile])

  const sortedHistory = useMemo(() => {
    if (!existingProfile?.vaccination_history) return []
    return [...existingProfile.vaccination_history].sort(
      (a, b) => (parseDateLocal(b.date_given)?.getTime() || 0) - (parseDateLocal(a.date_given)?.getTime() || 0)
    )
  }, [existingProfile])

  useEffect(() => {
    if (!existingProfile) return
    setRiskForm({
      gender: existingProfile.gender || '',
      is_pregnant: !!existingProfile.is_pregnant,
      is_immunocompromised: !!existingProfile.is_immunocompromised,
      has_diabetes: !!existingProfile.has_diabetes,
      has_chronic_lung: !!existingProfile.has_chronic_lung,
      has_heart_disease: !!existingProfile.has_heart_disease,
      has_chronic_kidney: !!existingProfile.has_chronic_kidney,
      has_chronic_liver: !!existingProfile.has_chronic_liver,
      has_asplenia: !!existingProfile.has_asplenia,
      has_hiv: !!existingProfile.has_hiv,
    })
  }, [existingProfile])

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const addRow = () => setHistory((h) => [...h, { vaccine_key: '', date_given: '' }])
  const removeRow = (i) => setHistory((h) => h.filter((_, idx) => idx !== i))
  const updateRow = (i, key, val) => setHistory((h) => h.map((r, idx) => (idx === i ? { ...r, [key]: val } : r)))

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const validHistory = inferDoseHistory(history)
      await createProfile({ ...form, vaccination_history: validHistory })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile.')
      setStep(1)
    } finally {
      setLoading(false)
    }
  }

  const submitAdditionalRecord = async () => {
    if (!addRecordForm.vaccine_key || !addRecordForm.date_given) {
      setAddRecordError('Please select a vaccine and date.')
      return
    }

    setAddRecordError('')
    setAddRecordSuccess('')
    setAddingRecord(true)

    try {
      const res = await addVaccinationRecord(addRecordForm)
      setExistingProfile(res.data)
      setAddRecordForm({ vaccine_key: '', date_given: '' })
      setAddRecordSuccess('Vaccination record added.')
    } catch (err) {
      setAddRecordError(err.response?.data?.detail || 'Failed to add vaccination record.')
    } finally {
      setAddingRecord(false)
    }
  }

  const handleDeleteRecord = async (recordId) => {
    const confirmed = window.confirm('Delete this vaccination record?')
    if (!confirmed) return

    setAddRecordError('')
    setAddRecordSuccess('')
    setDeletingRecordId(recordId)
    try {
      const res = await deleteVaccinationRecord(recordId)
      setExistingProfile(res.data)
      setAddRecordSuccess('Vaccination record deleted.')
    } catch (err) {
      setAddRecordError(err.response?.data?.detail || 'Failed to delete vaccination record.')
    } finally {
      setDeletingRecordId(null)
    }
  }

  const startEditDate = (row) => {
    setEditingDateId(row.id)
    setEditingDateValue(String(row.date_given).slice(0, 10))
    setAddRecordError('')
    setAddRecordSuccess('')
  }

  const cancelEditDate = () => {
    setEditingDateId(null)
    setEditingDateValue('')
  }

  const saveEditDate = async (recordId) => {
    if (!editingDateValue) {
      setAddRecordError('Please select a valid date.')
      return
    }
    setAddRecordError('')
    setAddRecordSuccess('')
    setUpdatingDateId(recordId)
    try {
      const res = await updateVaccinationRecordDate(recordId, { date_given: editingDateValue })
      setExistingProfile(res.data)
      setAddRecordSuccess('Vaccination date updated.')
      setEditingDateId(null)
      setEditingDateValue('')
    } catch (err) {
      setAddRecordError(err.response?.data?.detail || 'Failed to update vaccination date.')
    } finally {
      setUpdatingDateId(null)
    }
  }

  const toggleRisk = (key, value) => setRiskForm((s) => ({ ...s, [key]: value }))

  const saveRiskChanges = async () => {
    setRiskError('')
    setRiskSuccess('')
    setSavingRisks(true)
    try {
      const res = await updateProfile(riskForm)
      setExistingProfile(res.data)
      setEditingRisks(false)
      setRiskSuccess('Risk factors updated.')
    } catch (err) {
      setRiskError(err.response?.data?.detail || 'Failed to update risk factors.')
    } finally {
      setSavingRisks(false)
    }
  }

  if (loadingProfile) {
    return (
      <div className="page-loading">
        <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
        <p>Loading profile...</p>
      </div>
    )
  }

  if (existingProfile) {
    return (
      <div className="profile-view-page">
        <Navbar />
        <div className="profile-container profile-view-container">
          <div className="profile-header fade-up">
            <div className="profile-step-label">Patient Information</div>
            <h1>My Profile</h1>
            <p>Here is the information you already added.</p>
          </div>

          <div className="card profile-view-card fade-up">
            <div className="profile-view-grid">
              <div>
                <span className="profile-view-label">Full Name</span>
                <p>{existingProfile.name}</p>
              </div>
              <div>
                <span className="profile-view-label">Date of Birth</span>
                <p>{fmtDate(existingProfile.dob)}</p>
              </div>
              <div>
                <span className="profile-view-label">Gender</span>
                <p>{existingProfile.gender || 'Not provided'}</p>
              </div>
              <div>
                <span className="profile-view-label">Risk Factors</span>
                <p>{selectedRisks.length ? selectedRisks.join(', ') : 'None selected'}</p>
              </div>
            </div>
            <div className="profile-edit-actions">
              <button className="btn btn-outline" onClick={() => setEditingRisks((s) => !s)}>
                {editingRisks ? 'Cancel Edit' : 'Edit Risk Factors'}
              </button>
            </div>

            {editingRisks && (
              <div className="risk-edit-panel">
                <div className="form-group" style={{ maxWidth: 260 }}>
                  <label>Gender</label>
                  <select value={riskForm.gender} onChange={(e) => toggleRisk('gender', e.target.value)}>
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other / Prefer not to say</option>
                  </select>
                </div>
                <div className="risk-grid">
                  {RISK_FACTORS.map((rf) => (
                    <label key={rf.key} className={`risk-item ${riskForm[rf.key] ? 'checked' : ''}`}>
                      <input
                        type="checkbox"
                        checked={!!riskForm[rf.key]}
                        onChange={(e) => toggleRisk(rf.key, e.target.checked)}
                      />
                      <span className="risk-check">{riskForm[rf.key] ? 'X' : ''}</span>
                      {rf.label}
                    </label>
                  ))}
                </div>
                {riskError && <div className="error-msg">Error: {riskError}</div>}
                <div className="profile-edit-actions">
                  <button className="btn btn-primary" onClick={saveRiskChanges} disabled={savingRisks}>
                    {savingRisks ? <span className="spinner" /> : null}
                    Save Risk Changes
                  </button>
                </div>
              </div>
            )}

            {riskSuccess && <div className="success-msg" style={{ marginTop: 10 }}>{riskSuccess}</div>}
          </div>

          <div className="card profile-history-card fade-up">
            <h2 className="step-title" style={{ marginBottom: 12 }}>Vaccination History</h2>
            {sortedHistory.length === 0 ? (
              <div className="empty-history">No vaccination records found.</div>
            ) : (
              <div className="profile-history-table">
                <div className="profile-history-head">
                  <span>Vaccine</span>
                  <span>Dose</span>
                  <span>Date Given</span>
                  <span>Action</span>
                </div>
                {sortedHistory.map((row) => (
                  <div key={row.id} className="profile-history-row">
                    <span>{row.vaccine_name}</span>
                    <span>#{row.dose_number}</span>
                    <span>
                      {editingDateId === row.id ? (
                        <input
                          type="date"
                          className="date-edit-input"
                          value={editingDateValue}
                          max={new Date().toISOString().split('T')[0]}
                          onChange={(e) => setEditingDateValue(e.target.value)}
                        />
                      ) : (
                        fmtDate(row.date_given)
                      )}
                    </span>
                    <span>
                      <div className="record-actions">
                        {editingDateId === row.id ? (
                          <>
                            <button
                              className="btn btn-primary profile-small-btn"
                              onClick={() => saveEditDate(row.id)}
                              disabled={updatingDateId === row.id}
                            >
                              {updatingDateId === row.id ? <span className="spinner" /> : null}
                              Save
                            </button>
                            <button className="btn btn-outline profile-small-btn" onClick={cancelEditDate}>Cancel</button>
                          </>
                        ) : (
                          <button className="btn btn-outline profile-small-btn" onClick={() => startEditDate(row)}>
                            Edit Date
                          </button>
                        )}

                        <button
                          className="btn btn-danger profile-delete-btn"
                          onClick={() => handleDeleteRecord(row.id)}
                          disabled={deletingRecordId === row.id}
                        >
                          {deletingRecordId === row.id ? <span className="spinner" /> : null}
                          Delete
                        </button>
                      </div>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card profile-history-card fade-up">
            <h2 className="step-title" style={{ marginBottom: 12 }}>Add Vaccination Record</h2>
            <p className="step-desc" style={{ marginBottom: 14 }}>
              Add new doses even after profile setup. Dose number is inferred automatically.
            </p>
            <div className="history-row profile-add-row">
              <div className="form-group">
                <label>Vaccine</label>
                <select
                  value={addRecordForm.vaccine_key}
                  onChange={(e) => setAddRecordForm((f) => ({ ...f, vaccine_key: e.target.value }))}
                >
                  <option value="">Select vaccine...</option>
                  {VACCINES.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Date Given</label>
                <input
                  type="date"
                  value={addRecordForm.date_given}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setAddRecordForm((f) => ({ ...f, date_given: e.target.value }))}
                />
              </div>
              <button className="btn btn-primary add-record-btn" onClick={submitAdditionalRecord} disabled={addingRecord}>
                {addingRecord ? <span className="spinner" /> : null}
                Add Record
              </button>
            </div>

            {addRecordError && <div className="error-msg" style={{ marginTop: 10 }}>Error: {addRecordError}</div>}
            {addRecordSuccess && <div className="success-msg" style={{ marginTop: 10 }}>{addRecordSuccess}</div>}
          </div>
        </div>
      </div>
    )
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
            <div key={i} className={`step-item ${step === i + 1 ? 'active' : ''} ${step > i + 1 ? 'done' : ''}`}>
              <div className="step-circle">{step > i + 1 ? 'Done' : i + 1}</div>
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
                <div className="form-group" style={{ gridColumn: '1/-1' }}>
                  <label>Full Name *</label>
                  <input placeholder="John Smith" value={form.name} onChange={(e) => set('name', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Date of Birth *</label>
                  <input type="date" value={form.dob} onChange={(e) => set('dob', e.target.value)} max={new Date().toISOString().split('T')[0]} required />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select value={form.gender} onChange={(e) => set('gender', e.target.value)}>
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other / Prefer not to say</option>
                  </select>
                </div>
              </div>
              <div className="step-actions">
                <button className="btn btn-primary" onClick={() => setStep(2)} disabled={!form.name || !form.dob}>
                  {'Next: Risk Factors ->'}
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
                {RISK_FACTORS.map((rf) => (
                  <label key={rf.key} className={`risk-item ${form[rf.key] ? 'checked' : ''}`}>
                    <input type="checkbox" checked={form[rf.key]} onChange={(e) => set(rf.key, e.target.checked)} />
                    <span className="risk-check">{form[rf.key] ? 'X' : ''}</span>
                    {rf.label}
                  </label>
                ))}
              </div>
              <div className="step-actions">
                <button className="btn btn-outline" onClick={() => setStep(1)}>Back</button>
                <button className="btn btn-primary" onClick={() => setStep(3)}>{'Next: Vaccine History ->'}</button>
              </div>
            </div>
          )}

          {/* STEP 3 — Vaccination History */}
          {step === 3 && (
            <div className="step-content">
              <h2 className="step-title">Vaccination History</h2>
              <p className="step-desc">Add vaccines already received. Dose numbers are inferred from dates per vaccine.</p>

              {history.length === 0 && <div className="empty-history">No vaccination records added yet.</div>}

              {history.map((row, i) => (
                <div key={i} className="history-row">
                  <div className="form-group">
                    <label>Vaccine</label>
                    <select value={row.vaccine_key} onChange={(e) => updateRow(i, 'vaccine_key', e.target.value)}>
                      <option value="">Select vaccine...</option>
                      {VACCINES.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Date Given</label>
                    <input
                      type="date"
                      value={row.date_given}
                      max={new Date().toISOString().split('T')[0]}
                      onChange={(e) => updateRow(i, 'date_given', e.target.value)}
                    />
                  </div>
                  <button className="btn btn-danger remove-btn" onClick={() => removeRow(i)}>Remove</button>
                </div>
              ))}

              <button className="btn btn-outline add-btn" onClick={addRow}>+ Add Vaccine Record</button>

              {error && <div className="error-msg" style={{ marginTop: 16 }}>Error: {error}</div>}

              <div className="step-actions">
                <button className="btn btn-outline" onClick={() => setStep(2)}>Back</button>
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
