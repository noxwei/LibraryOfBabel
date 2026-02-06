'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, Code, Menu, X, Upload, Search, Library } from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { href: '/demo', label: 'Demo', icon: Search },
  { href: '/browse', label: 'Browse', icon: Library },
  { href: '/api-docs', label: 'API', icon: Code },
  { href: '/upload', label: 'Upload', icon: Upload },
]

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  return (
    <header className="bg-bg-card border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-model-technical" />
            <span className="font-bold text-xl">LibraryOfBabel</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 transition-colors ${
                  pathname === href
                    ? 'text-model-technical'
                    : 'text-text-secondary hover:text-model-technical'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Nav */}
        {mobileMenuOpen && (
          <nav className="md:hidden py-4 border-t border-gray-800">
            <div className="flex flex-col gap-4">
              {navItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 ${
                    pathname === href ? 'text-model-technical' : 'text-text-secondary'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              ))}
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
