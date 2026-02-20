/* ==========================================
 * File: frontend/src/components/QdocLegacySection.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import './QdocLegacySection.css'
import qdocLogo from '../assets/qdoc-logo.png'
import qdocFamily from '../assets/qdoc-family.webp'

function FooterCol({ title, items }) {
  return (
    <div className="qdoc-legacy-col">
      <h4>{title}</h4>
      {items.map((item) => <p key={item}>{item}</p>)}
    </div>
  )
}

export default function QdocLegacySection() {
  return (
    <section className="qdoc-legacy">
      <div className="qdoc-legacy-top">
        <div className="qdoc-legacy-copy">
          <h3>QDOC VIRTUAL HEALTHCARE</h3>
          <p>
            See a provider online now, from the comfort of your own home.
            QDoc is a free, provincially funded online platform that connects
            patients to local doctors and nurse practitioners by video.
          </p>
          <a className="qdoc-legacy-btn" href="https://qdoc.ca" target="_blank" rel="noreferrer">
            SEE A PROVIDER NOW
          </a>
        </div>
        <img src={qdocFamily} alt="QDoc virtual care" className="qdoc-legacy-image" />
      </div>

      <div className="qdoc-legacy-grid">
        <div className="qdoc-legacy-brand">
          <img src={qdocLogo} alt="QDoc" />
          <p>
            We&apos;re on a mission to ensure equal access to quality medical care
            for all Canadians, regardless of geographic location.
          </p>
        </div>
        <FooterCol title="Serving" items={['Brandon', 'Steinbach', 'Thompson', 'Winnipeg', 'Kenora', 'Thunder Bay']} />
        <FooterCol title="Regions" items={['Interlake Eastern', 'Northern Health', 'Prairie Mountain', 'Southern Health', 'Nuvanut']} />
        <FooterCol title="Resources" items={['Crisis Support', 'How It Works', 'Pricing', 'What’s New', 'Blog']} />
        <FooterCol title="Get In Touch" items={['804-213 Notre Dame Ave, Winnipeg, MB', 'Email: info@qdoc.ca', 'Support: 1 833 736 2362', 'Mon-Fri 8:30AM - 4:30PM CST']} />
      </div>

      <div className="qdoc-legacy-bottom">
        <p>QDoc&apos;s offices are located on the lands of Anishinaabe, Ininiwak, and the National Homeland of the Red River Métis.</p>
        <p>Copyright © QDoc Inc 2026</p>
      </div>
    </section>
  )
}

