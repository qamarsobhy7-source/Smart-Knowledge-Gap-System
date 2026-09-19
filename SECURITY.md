# Security Policy

## 🛡️ Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes    |
| < 1.0   | ❌ No     |

---

## 🚨 Reporting a Vulnerability

**Please DO NOT report security vulnerabilities via public GitHub issues.**

### How to Report

If you discover a security vulnerability, please:

1. **Use GitHub's private reporting** — [Report a vulnerability](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/security/advisories/new)
2. **Or email us directly** with the details

### What to Include

Please provide:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact info** (for follow-up)

### What to Expect

| Timeline | Action |
|----------|--------|
| **Within 48h** | Acknowledgment of receipt |
| **Within 7 days** | Initial assessment & severity rating |
| **Within 30 days** | Fix deployed (if applicable) |
| **After fix** | Public disclosure (with your permission) |

---

## 🔒 Security Measures in Place

### Authentication & Sessions

- **Password hashing** — Werkzeug PBKDF2 with salt
- **Session cookies** — `HttpOnly`, `Secure`, `SameSite=Lax`
- **Session lifetime** — 1 hour with auto-expiry
- **CSRF protection** — tokens on all POST forms
- **Password reset** — time-limited signed tokens

### Data Protection

- **Parameterized SQL queries** — prevents SQL injection
- **Environment variables** — no secrets in source code
- **Input validation** — server-side on all endpoints
- **Output escaping** — Jinja2 auto-escape by default

### API & External Services

- **Rate limiting** — on auth & chat endpoints
- **HTTPS only** — enforced in production
- **API keys** — scoped and rotated regularly
- **Qdrant/Supabase** — TLS encrypted connections

### Infrastructure

- **Docker** — isolated containers
- **Gunicorn** — production WSGI server
- **Faable Cloud** — GDPR-compliant hosting in Europe
- **Dependencies** — monitored for CVEs via GitHub Dependabot

---

## 🚫 Out of Scope

The following are considered **out of scope** for security reports:

- Denial of Service (DoS) attacks requiring excessive resources
- Social engineering attacks against users
- Issues in third-party dependencies (report upstream)
- Missing security headers on non-production environments
- Self-XSS or issues requiring physical device access
- Reports from automated scanners without proof-of-concept

---

## 🏆 Recognition

We appreciate responsible disclosure. Contributors who report valid vulnerabilities will be:

- Credited in the security advisory (with permission)
- Listed in our [Security Acknowledgments](#)
- Given priority support for their own contributions

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)

---

## 📞 Contact

For security-related inquiries:

- **GitHub:** [@qamarsobhy7-source](https://github.com/qamarsobhy7-source)
- **Private Report:** [Security Advisory](https://github.com/qamarsobhy7-source/Smart-Knowledge-Gap-System/security/advisories/new)

---

**Thank you for helping keep this project and its users safe! 🔒**
