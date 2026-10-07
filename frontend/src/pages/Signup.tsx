import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD_LENGTH = 8

export default function Signup() {
  const { user, signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) return <Navigate to="/" replace />

  const update = (e: ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  const mismatch = form.confirm.length > 0 && form.password !== form.confirm

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (form.password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      const { confirm: _confirm, ...input } = form
      await signup(input)
      navigate('/', { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <div className="page auth">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Join Campus Customs</h1>
        <p className="muted">Create an account so our assistant remembers you.</p>
        <div className="row-2">
          <label>
            First name
            <input name="first_name" required autoComplete="given-name" value={form.first_name} onChange={update} />
          </label>
          <label>
            Last name
            <input name="last_name" required autoComplete="family-name" value={form.last_name} onChange={update} />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            name="email"
            required
            placeholder="you@yale.edu"
            autoComplete="email"
            value={form.email}
            onChange={update}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            required
            minLength={MIN_PASSWORD_LENGTH}
            autoComplete="new-password"
            value={form.password}
            onChange={update}
          />
          <span className="hint">At least {MIN_PASSWORD_LENGTH} characters.</span>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            name="confirm"
            required
            autoComplete="new-password"
            value={form.confirm}
            onChange={update}
            aria-invalid={mismatch}
            className={mismatch ? 'input-bad' : undefined}
          />
          {mismatch && <span className="hint hint-bad">Passwords don't match yet.</span>}
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn-pink btn-block" type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
        <p className="muted small">
          Already have an account?{' '}
          <Link to="/login" className="link-pink">
            Log in
          </Link>
        </p>
      </form>
    </div>
  )
}
