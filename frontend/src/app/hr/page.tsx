"use client";

import Link from "next/link";
import HRDashboard from "../../components/hr/HRDashboard";

export default function HRPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            HR Management System
          </h1>
          <p className="text-gray-600">
            Managed by Linda Zhang (张丽娜) - HR Operations & Agent Performance
          </p>
        </div>

        <HRDashboard />

        <div className="mt-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            ← Back to Library Search
          </Link>
        </div>
      </div>
    </div>
  );
}
