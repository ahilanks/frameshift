"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Upload", href: "/" },
  { name: "Projects", href: "/projects" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">F</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Frameshift</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-blue-600",
                  pathname === item.href
                    ? "text-blue-600 border-b-2 border-blue-600 pb-1"
                    : "text-gray-700"
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>

          {/* CTA */}
          <div className="flex items-center space-x-4">
            <Link
              href="/"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              New Project
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}