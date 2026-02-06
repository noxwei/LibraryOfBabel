'use client'

import Link from 'next/link'
import { Shield, Search, Server } from 'lucide-react'
import { motion } from 'framer-motion'

const audiences = [
  { label: 'NGOs & Nonprofits', icon: Shield },
  { label: 'Academic Research', icon: Search },
  { label: 'Enterprise', icon: Server },
]

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-model-technical/5 to-transparent pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 pt-20 pb-16 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="text-center"
        >
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
            Your Documents. Your Infrastructure.{' '}
            <span className="text-model-technical">Your AI.</span>
          </h1>

          <p className="text-text-secondary text-lg sm:text-xl max-w-3xl mx-auto mb-10 leading-relaxed">
            Offline RAG for organizations that can&apos;t send data to the cloud. Search, analyze,
            and retrieve from your own document corpus — entirely on your hardware.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 px-8 py-3 bg-model-technical text-white font-semibold rounded-lg
                         hover:bg-model-technical/90 transition-colors text-lg"
            >
              <Search className="w-5 h-5" />
              Try Live Demo
            </Link>
            <Link
              href="/api-docs"
              className="inline-flex items-center gap-2 px-8 py-3 border border-gray-600 text-text-primary font-semibold rounded-lg
                         hover:border-model-technical hover:text-model-technical transition-colors text-lg"
            >
              API Documentation
            </Link>
          </div>

          {/* Audience badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-wrap items-center justify-center gap-3"
          >
            {audiences.map(({ label, icon: Icon }) => (
              <span
                key={label}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-bg-card border border-gray-800 text-text-secondary text-sm"
              >
                <Icon className="w-4 h-4 text-model-technical" />
                {label}
              </span>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
