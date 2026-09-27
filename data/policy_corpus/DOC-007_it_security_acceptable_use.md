# IT Security, Equipment, and Acceptable Use Policy

**Document ID:** DOC-007  
**Effective Date:** January 1, 2024  
**Last Revised:** August 25, 2024  
**Owner:** Information Security & IT Infrastructure  
**Applicability:** All Global Employees, Contractors, and Third Parties  

---

## 1. Purpose and Scope
This policy defines the standards and acceptable behaviors for safeguarding Quantic Global Enterprises' information assets, computing hardware, communication networks, and proprietary intellectual property against unauthorized access, loss, or security compromise.

## 2. Company Hardware and Asset Management

### 2.1 Corporate Device Provisioning
All full-time employees are provisioned with standardized company-owned computing hardware (laptops, mobile devices, and security keys) managed via Mobile Device Management (MDM) software. Company devices remain the exclusive property of the enterprise and must be surrendered immediately upon separation of employment.

### 2.2 Prohibited Hardware Modifications
Employees are strictly prohibited from:
* Disabling, modifying, or circumventing endpoint detection and response (EDR), disk encryption (FileVault/BitLocker), or corporate antivirus agents.
* Jailbreaking, rooting, or installing unauthorized operating system modifications on company hardware.
* Connecting unapproved external mass-storage devices (USB drives, personal external hard drives) without Infosec clearance.

## 3. Password Standards and Multi-Factor Authentication (MFA)

### 3.1 Authentication Requirements
* **Multi-Factor Authentication:** MFA is mandatory for accessing all enterprise cloud applications, Single Sign-On (SSO) gateways, email, and virtual private network (VPN) tunnels. Authentication via hardware security key (FIDO2/WebAuthn) or corporate authenticator app is required; SMS-based verification is deprecated and disallowed.
* **Password Complexity:** Master SSO passwords must be at least sixteen (16) characters long, containing upper- and lower-case letters, numbers, and symbols. Passwords must not be reused across services.

### 3.2 Password Sharing Prohibition
Credentials and security tokens must never be shared between employees, written down in unsecured locations, or hardcoded into source code repositories or configuration files.

## 4. Network and Remote Access Security

### 4.1 Corporate VPN Requirement
When connecting to internal production networks, staging environments, or confidential databases from remote locations or public networks, employees must establish a secure connection using the corporate Zero-Trust Network Access (ZTNA) or corporate VPN client.

### 4.2 Public Wi-Fi Restrictions
Employees traveling or working remotely are strictly prohibited from accessing unencrypted or public Wi-Fi networks (e.g., hotel, airport, or coffee shop networks) unless the connection is fully routed through the corporate VPN client.

## 5. Data Classification and Acceptable Use

### 5.1 Classification Levels
Enterprise data is classified into three tiers:
1. **Public:** Information authorized for public dissemination (press releases, marketing brochures).
2. **Internal:** Standard business communications, organizational charts, internal guides.
3. **Restricted / Confidential:** Customer Personally Identifiable Information (PII), proprietary code, financial audit files, passwords, and executive strategic plans.

### 5.2 Generative AI and Third-Party Cloud Services
Employees must not input or transmit Restricted or Confidential company data, source code, customer records, or employee personal data into unapproved third-party commercial generative AI tools, consumer chatbots, or personal cloud storage accounts (such as personal Google Drive or Dropbox).

## 6. Incident Reporting and Lost Equipment Protocol
Any suspected security breach, phishing email, unauthorized access, malware infection, or physical loss/theft of a corporate device must be reported immediately to security@quantic-global.internal or through the IT Emergency Hotline within two (2) hours of discovery. Prompt reporting enables immediate remote device wiping to safeguard customer data.
