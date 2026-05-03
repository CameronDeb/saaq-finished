import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // load from localStorage on mount
    try {
      const saved = localStorage.getItem('saaq_auth')
      if (saved) {
        const parsed = JSON.parse(saved)
        setUser(parsed)
        // verify token is still valid
        api.getMe().then(profile => {
          const updated = { ...parsed, ...profile }
          setUser(updated)
          localStorage.setItem('saaq_auth', JSON.stringify(updated))
        }).catch(() => {
          localStorage.removeItem('saaq_auth')
          setUser(null)
        })
      }
    } catch {}
    setLoading(false)

    // listen for forced logout
    const handleLogout = () => { setUser(null) }
    window.addEventListener('saaq_logout', handleLogout)
    return () => window.removeEventListener('saaq_logout', handleLogout)
  }, [])

  const login = async (email, password) => {
    const result = await api.login({ email, password })
    setUser(result)
    localStorage.setItem('saaq_auth', JSON.stringify(result))
    return result
  }

  const signup = async (email, password, fullName) => {
    const result = await api.signup({ email, password, full_name: fullName })
    setUser(result)
    localStorage.setItem('saaq_auth', JSON.stringify(result))
    return result
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('saaq_auth')
  }

  const isAdmin = user?.role === 'admin'
  const isAuthenticated = !!user?.access_token

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading, isAdmin, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
