# Security Policy

Phylaworld takes security seriously. If you find a vulnerability in the
project, we ask that you report it responsibly so it can be fixed before it is
publicly disclosed.

## Supported Versions

Phylaworld is in active development (pre-1.0). Because the project changes
rapidly, security fixes are generally provided for the latest development
version only. Before dependency upgrades and major milestones are tagged, any
known security issues are prioritized and addressed.

| Version                | Supported          |
| ---------------------- | ------------------ |
| Latest development     | :white_check_mark: |
| Tagged release values  | :white_check_mark: |
| Older releases         | :x:                |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.** Report
them privately.

Preferred method — **GitHub Private Vulnerability Reporting**:

1. Go to the **Security** tab of this repository.
2. Click **Report a vulnerability**.
3. Fill out the form with as much detail as you can.

Alternative method: email the maintainers at
[INSERT SECURITY CONTACT EMAIL].

### What to include

- Which component and version is affected.
- A clear description of the vulnerability and its impact.
- Steps to reproduce, or a proof-of-concept.
- Whether you have a patch or proposed fix.
- Your contact details (optional, but helpful).

### What to expect

- You will receive an acknowledgment within **3–5 business days**.
- You will receive updates on the fix and disclosure timeline as work
  progresses.
- We will credit you in the advisory/release notes if you wish, and will ask
  before disclosing your identity.

## Disclosure Policy

- We coordinate disclosure with the reporter and work toward a fix before
  public posting.
- Once a fix is available, we publish a security advisory following
  [GitHub's coordinated disclosure guidelines](https://docs.github.com/en/code-security/security-advisories/working-with-security-advisories-and-a-vulnerable-repository-on-github/about-coordinated-disclosure-of-security-vulnerabilities).
- Security-related fixes are labeled `security` in the changelog when
  applicable.

## Scope

This policy covers the Phylaworld codebase, including all `res://` project
files, scripts, and build/export configuration committed to this repository.
It also applies to the infrastructure and tooling the project publishes under
this repository.

Out of scope: third-party tools and assets not distributed by this project,
issues specific to unpatched Godot engine releases (report those directly to
[the Godot project](https://github.com/godotengine/godot/security)), and
Apple-platform-specific code, since Apple devices are not officially supported.

## Safe Harbor

We support good-faith security research. If you report a vulnerability in
accordance with this policy, we will not pursue legal action against you for
that research. Malicious behavior, data destruction, or actions that harm
other users are not covered.

---

*Thank you for helping keep Phylaworld safe.*