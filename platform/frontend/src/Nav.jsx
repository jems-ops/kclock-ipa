import { useState, useEffect } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'

const links = [
  { to: '/dashboard',  label: 'Apps' },
  { to: '/onboarding', label: 'Onboarding' },
  { to: '/diagnose',   label: 'Diagnose' },
  { to: '/compliance', label: 'Compliance' },
  { to: '/audit',      label: 'Audit' },
  { to: '/docs',       label: 'API Docs' },
]

export default function Nav() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  const linkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors px-3 py-1.5 rounded-lg ${
      isActive ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400 hover:text-white hover:bg-white/5'
    }`

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 ${scrolled ? 'glass shadow-lg' : 'bg-gray-950/80 backdrop-blur'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-white hover:text-indigo-400 transition-colors">
          ⬡ IPA Platform
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {links.map(l => <NavLink key={l.to} to={l.to} className={linkClass}>{l.label}</NavLink>)}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <Link to="/dashboard" className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium transition-colors">
            Dashboard →
          </Link>
        </div>

        <button className="md:hidden p-2 text-slate-400 hover:text-white" onClick={() => setOpen(o => !o)}>
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden glass border-t border-slate-800">
          <nav className="flex flex-col p-4 gap-1">
            {links.map(l => (
              <NavLink key={l.to} to={l.to} className={linkClass} onClick={() => setOpen(false)}>
                {l.label}
              </NavLink>
            ))}
            <Link to="/dashboard" onClick={() => setOpen(false)}
              className="mt-2 text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium text-center">
              Dashboard →
            </Link>
          </nav>
        </div>
      )}
    </header>
  )
}
