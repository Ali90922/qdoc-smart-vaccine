import { useMemo, useState } from 'react'
import Navbar from '../components/Navbar'
import { VACCINE_ENCYCLOPEDIA } from '../data/vaccineEncyclopedia'
import './Encyclopedia.css'

function DetailCard({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="card enc-card">
      <button className="enc-card-toggle" onClick={() => setOpen(v => !v)}>
        <span>{title}</span>
        <span className="enc-toggle-mark">{open ? '-' : '+'}</span>
      </button>
      {open && <div className="enc-card-body">{children}</div>}
    </section>
  )
}

export default function Encyclopedia() {
  const [active, setActive] = useState(VACCINE_ENCYCLOPEDIA[0]?.id || '')

  const selected = useMemo(
    () => VACCINE_ENCYCLOPEDIA.find(v => v.id === active) || VACCINE_ENCYCLOPEDIA[0],
    [active]
  )

  return (
    <div className="encyclopedia-page">
      <Navbar />
      <div className="encyclopedia-container">
        <header className="enc-header fade-up">
          <h1>Vaccine Encyclopedia</h1>
          <p>
            Manitoba-aligned vaccine reference extracted from the provided policy document.
            Select a vaccine tab to view eligibility and rule details.
          </p>
        </header>

        <section className="enc-tabs-wrap fade-up">
          <div className="enc-tabs" role="tablist" aria-label="Vaccine tabs">
            {VACCINE_ENCYCLOPEDIA.map(v => (
              <button
                key={v.id}
                role="tab"
                aria-selected={active === v.id}
                className={`enc-tab ${active === v.id ? 'active' : ''}`}
                onClick={() => setActive(v.id)}
              >
                {v.tabLabel}
              </button>
            ))}
          </div>
        </section>

        {selected && (
          <>
            <section className="card enc-hero fade-up">
              <div className="enc-hero-top">
                <div>
                  <div className="enc-id">{selected.id}</div>
                  <h2>{selected.name}</h2>
                </div>
                <div className="enc-source">Source: {selected.source}</div>
              </div>
              <p className="enc-summary">{selected.summary}</p>
            </section>

            <section className="card enc-facts fade-up">
              <h3>Key Facts</h3>
              <div className="enc-facts-grid">
                <div><span>Min Age</span><strong>{selected.keyFacts.minAge}</strong></div>
                <div><span>Max Age</span><strong>{selected.keyFacts.maxAge}</strong></div>
                <div><span>Doses Required</span><strong>{selected.keyFacts.dosesRequired}</strong></div>
                <div><span>Dose Interval</span><strong>{selected.keyFacts.doseInterval}</strong></div>
                <div><span>Repeat Interval</span><strong>{selected.keyFacts.repeatInterval}</strong></div>
                <div><span>Risk Factors</span><strong>{selected.keyFacts.riskFactors}</strong></div>
                <div><span>Contraindications</span><strong>{selected.keyFacts.contraindications}</strong></div>
                <div><span>Pregnancy Safe</span><strong>{selected.keyFacts.pregnancySafe}</strong></div>
              </div>
            </section>

            <DetailCard title="Rules and Constraints" defaultOpen>
              <ul className="enc-rules-list">
                {selected.rules.map((rule, idx) => (
                  <li key={`${selected.id}-rule-${idx}`}>{rule}</li>
                ))}
              </ul>
            </DetailCard>

            <DetailCard title="Reference Notes">
              <p>
                This page is informational and reflects the reference PDF content provided for this project.
                Final eligibility decisions should always follow your active rule engine and policy governance process.
              </p>
            </DetailCard>
          </>
        )}
      </div>
    </div>
  )
}
