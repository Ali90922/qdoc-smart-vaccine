import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, signup } from '../api'
import './Landing.css'
import qdocLogo from '../assets/qdoc-logo.png'

export default function Landing() {
  const navigate      = useNavigate()
  const [mode, setMode]     = useState('login')   // 'login' | 'signup'
  const [email, setEmail]   = useState('')
  const [pass, setPass]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const fn   = mode === 'login' ? login : signup
      const res  = await fn({ email, password: pass })
      const data = res.data
      localStorage.setItem('token', data.token)
      localStorage.setItem('user_id', data.user_id)
      // If new user → profile creation; else → dashboard
      navigate(data.is_new_user ? '/profile' : '/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="landing">
      {/* Background grid */}
      <div className="landing-bg" />

      <div className="landing-left">
        <img src={qdocLogo} alt="QDoc" className="hero-logo" />
        <div className="hero-tag">Manitoba Immunization Program</div>
        <h1 className="hero-title">
          Preventive care,<br />
          powered by <span className="hero-accent">QDoc.</span>
        </h1>
        <p className="hero-sub">
          QDoc tracks your immunization history, checks Manitoba eligibility rules,
          and tells you exactly what's due — before you miss it.
        </p>
        <div className="hero-stats">
          <div className="stat"><span>15+</span> Vaccines tracked</div>
          <div className="stat"><span>100%</span> MB guidelines</div>
          <div className="stat"><span>Real-time</span> Reminders</div>
        </div>
      </div>

      <div className="landing-right">
        <div className="auth-card card fade-up">
          <div className="auth-tabs">
            <button className={`auth-tab ${mode === 'login' ? 'active' : ''}`} onClick={() => { setMode('login'); setError('') }}>Sign In</button>
            <button className={`auth-tab ${mode === 'signup' ? 'active' : ''}`} onClick={() => { setMode('signup'); setError('') }}>Create Account</button>
          </div>

          <form onSubmit={submit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={pass}
                onChange={e => setPass(e.target.value)}
                required
                minLength={6}
              />
            </div>

            {error && <div className="error-msg">⚠ {error}</div>}

            <button className="btn btn-primary w-full" type="submit" disabled={loading}>
              {loading ? <span className="spinner" /> : null}
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <p className="auth-note">
            {mode === 'login'
              ? "Don't have an account? "
              : 'Already registered? '}
            <button className="link-btn" onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError('') }}>
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
