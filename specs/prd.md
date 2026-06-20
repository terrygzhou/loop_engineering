# Glory EV — Customer App Product Requirements Document (PRD)

> **Document Version:** 1.0  
> **Date:** 2026-06-01  
> **Status:** Draft — Stage 1 of 6-stage build pipeline  
> **Owner:** Product Management  
> **Next Stage:** UI/UX Design (Stage 2)

---

## Table of Contents

1. [Product Vision & Target Users](#1-product-vision--target-users)
2. [Feature Breakdown by User Story](#2-feature-breakdown-by-user-story)
3. [User Flow Diagrams](#3-user-flow-diagrams)
4. [Screen Inventory](#4-screen-inventory)
5. [Acceptance Criteria per Feature](#5-acceptance-criteria-per-feature)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Out of Scope for MVP](#7-out-of-scope-for-mvp)
8. [Prioritized Feature List: MVP vs Phase 2](#8-prioritized-feature-list-mvp-vs-phase-2)
9. [Technical Constraints & Stack](#9-technical-constraints--stack)
10. [Appendix: Glossary & References](#10-appendix-glossary--references)

---

## 1. Product Vision & Target Users

### 1.1 Product Vision

Glory EV Customer App is a branded, mobile-first digital platform that empowers electric vehicle customers to explore, configure, purchase, and maintain their vehicles through a single unified interface — from first awareness through the entire vehicle lifecycle. It eliminates the friction of fragmented websites, phone calls, and dealership visits by providing a self-service, transparent, and seamless digital experience.

### 1.2 Mission Statement

Enable every Glory EV customer to feel confident, informed, and in control at every touchpoint of their EV journey — from discovery to delivery to maintenance — through a single, beautifully designed digital platform.

### 1.3 Target Users

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| **Prospective Buyer (Awareness Phase)** | EV-curious consumer researching vehicles online. Not yet committed to a purchase. | Explore vehicle specs, compare models, understand pricing, gauge availability. |
| **Evaluating Customer (Evaluation Phase)** | Interested buyer ready to test-drive and shortlist. | Book test drives, compare configurations, evaluate financing options. |
| **Purchasing Customer (Purchase Phase)** | Committed buyer configuring, paying deposit, and tracking order. | Configure vehicle, select finance/lease, pay securely, monitor build progress. |
| **Vehicle Owner (Post-Purchase Phase)** | Delivered vehicle owner needing ongoing support. | Book service, view service history, access warranty info, receive reminders. |
| **Admin / Dealership Staff (Internal)** | Dealership personnel managing bookings, orders, and deliveries. | Manage test drive schedules, update order statuses, handle delivery handovers. *(Internal admin portal — separate scope)* |

### 1.4 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Time-to-first-interaction (app load) | < 2 seconds | Lighthouse / RUM monitoring |
| Test drive booking conversion rate | > 30% of browsing users | Analytics funnel |
| Order status check frequency | ≥ 2 checks/week per active order | API usage telemetry |
| Customer portal adoption | ≥ 20% of total leads within 30 days | Authenticated session tracking |
| Support ticket reduction | ≥ 40% decrease post-launch | Helpdesk system comparison |
| CSAT score | ≥ 4.2 / 5.0 | Post-interaction surveys |

---

## 2. Feature Breakdown by User Story

### US-1: Vehicle Exploration & Discovery (Awareness Phase)

> *As a Customer, I want to explore vehicle specifications, real-time availability, and transparent pricing through a responsive web and mobile interface, so that I can make informed initial decisions during the awareness phase without visiting a dealership.*

**Features:**
- **Vehicle Catalog Browsing** — Grid/list view of available models with thumbnail images, key specs (range, drive type, charging speed), and starting price.
- **Vehicle Detail View** — Full specification sheet, image gallery, color/trim options, and availability status for each model.
- **Search & Filtering** — Search by model name; filter by brand, price range, body type, battery range, drivetrain.
- **AI-Powered Recommendations** — Semantic search and personalized suggestions powered by Qdrant vector store ("Show me family SUVs with long range").
- **Real-Time Availability** — Stock/lead-time indicators per configuration per dealership region.
- **Transparent Pricing** — Display of on-road price breakdown (base price + options + taxes) with no hidden fees.

### US-2: Self-Service Portal & Account Management

> *As a Customer, I want a branded mobile app and web portal to view my order status, book test drives/services, and access my documents, so that I have a seamless, self-service experience without relying on phone calls or fragmented websites.*

**Features:**
- **User Registration & Authentication** — Email/phone signup, OTP verification, secure session management.
- **Customer Dashboard** — Personalized landing page showing active orders, upcoming bookings, recent notifications.
- **Document Access** — Download/view purchase agreements, invoices, warranty certificates, service records as PDFs.
- **Profile Management** — Edit contact details, manage notification preferences, update password.

### US-3: Test Drive Booking & Management (Evaluation Phase)

> *As a Customer, I want to seamlessly book and manage test drives with digital confirmation, vehicle details, and location routing, so that I can evaluate vehicles conveniently and reduce scheduling friction during the evaluation phase.*

**Features:**
- **Test Drive Booking** — Select vehicle, choose dealership location, pick date/time slot, submit request.
- **Availability Calendar** — Visual calendar showing open/occupied time slots per vehicle per location.
- **Digital Confirmation** — Instant booking confirmation with QR code, vehicle details, location map link.
- **Booking Management** — View upcoming bookings, reschedule or cancel within policy window.
- **Location Routing** — Integrated map link (Google Maps/Apple Maps) for directions to the dealership.
- **Post-Test Drive Feedback** — Optional rating/survey form after completed test drive.

### US-4: Vehicle Configuration, Purchase & Order Tracking (Purchase Phase)

> *As a Customer, I want to configure my vehicle, select finance/lease options, securely pay deposits, and track my order status in real-time through a unified portal, so that I have full transparency and control throughout the purchasing process.*

**Features:**
- **Vehicle Configurator** — Interactive tool to select trim, color, wheels, interior, tech packages with live price update.
- **Finance/Lease Calculator** — Input down payment, term length, credit tier; receive estimated monthly payments for buy vs. lease.
- **Secure Deposit Payment** — Integrated payment gateway (Stripe/PayPal) for deposits and full payments.
- **Order Status Tracker** — Timeline view of order milestones (Received → Approved → In Production → In Transit → Arrived → Ready for Delivery).
- **Milestone Notifications** — Push/SMS/email alerts at each status change.
- **Trade-In Valuation** *(Phase 2)* — Input current vehicle details for instant trade-in estimate.

### US-5: Delivery Notification & Digital Handover

> *As a Customer, I want automated notifications when my vehicle arrives, along with a digital handover experience including e-signatures, document access, and delivery scheduling, so that I can collect my vehicle efficiently without paperwork delays.*

**Features:**
- **Arrival Notification** — Automated push/SMS/email when vehicle arrives at dealership.
- **Delivery Scheduling** — Book a specific pickup/delivery date and time slot.
- **Digital Handover** — In-app e-signature for delivery documents (DIN, insurance handover, keys receipt).
- **Document Pack** — Pre-loaded delivery documents (registration, warranty, owner's manual) available for download.
- **Handover Checklist** — Interactive checklist for the customer to confirm vehicle condition at pickup.

### US-6: Vehicle Service & Maintenance (Post-Purchase Phase)

> *As a Customer, I want to view my vehicle's service history, book maintenance appointments, receive proactive reminders, and access warranty information through the same platform, so that I can maintain my vehicle seamlessly throughout its lifecycle.*

**Features:**
- **Service History Timeline** — Chronological view of all past services with details (date, dealer, work performed, cost).
- **Service Booking** — Select service type, pick date/time/location, submit request.
- **Proactive Reminders** — Push/SMS/email notifications for upcoming service due dates, warranty expiry, recall notices.
- **Warranty Information** — View active warranty coverage, terms, claims process.
- **Emergency roadside assist** *(Phase 2)* — One-tap SOS contact and dispatch via the app.

---



---

## 2b. Additional Features (Beyond Original MVP)

### US-7: Car Hiring / Rental

> *As a Customer, I want to rent a Glory EV vehicle for short-to-medium terms (1 week to 12+ months) before committing to purchase, so that I can experience daily EV ownership risk-free.*

**Features:**
- **Hireable Vehicle Browse** — Grid of available demo/pool vehicles with specs and weekly rates
- **Plan Selection** — 4 plans: Trial Week (7-14 days), Short Term (14-28 days), Medium Term (30-180 days), Long Term (180+ days)
- **Membership Discount Integration** — Tier-based discounts (Bronze: 0%, Silver: 5%, Gold: 10%, Platinum: 15%, Diamond: 20%)
- **Application Form** — Driver licence, secondary ID, pickup details, T&C acceptance
- **Hire Lifecycle** — Pending → Under Review → Approved → Paid → Active → Returned → Completed
- **Hireable Vehicle Filter** — Only `delivered`, `used`, or `returned` units are hireable (excludes `allocated` sold vehicles)

### US-8: Membership & Loyalty Program

> *As a Customer, I want to earn points and unlock tier benefits across my EV journey, so that I feel rewarded for engagement and have motivation to stay loyal.*

**Features:**
- **5-Tier System** — Bronze (0), Silver (500), Gold (2500), Platinum (10000), Diamond (50000) points
- **Point Earning** — Purchase (100 pts/$1000), Test Drive (50 pts), Service (100 pts), Review (10 pts), Referral (200 pts)
- **Tier Benefits** — Priority booking, exclusive events, free services, extended warranty, birthday rewards
- **Rewards Catalog** — 10% Off Accessory Shop (500), Free Full Service (1000), Free Tire Rotation (250), 20% Off Charging Cable (1000), $50 Fuel Voucher (250)
- **Auto-Enrollment** — New users auto-enrolled at Bronze tier
- **Points History** — Track earned, redeemed, current balance, tier progression

### US-9: Customer Care Portal

> *As a Customer, I want to access self-service support through FAQs, case management, and enquiries, so that I can get help without calling the dealership.*

**Features:**
- **FAQ Database** — Categorized searchable FAQs (warranty, battery, charging, delivery, service, financing)
- **Support Case Management** — Create cases with type/priority/severity, track status, add messages
- **Case Types** — billing, technical, service, delivery, product_enquiry, complaint, general
- **Case Priorities** — low, medium, high, urgent
- **Case Status Tracking** — open → in_progress → resolved → closed
- **General Enquiries** — Lightweight enquiry form for non-case questions

---

## 10b. Additional Glossary Terms

| Term | Definition |
|------|-----------|
| **Hiring** | Car rental/subscription agreement between customer and Glory EV |
| **HiringPlan** | Rental plan definition with duration, rate, and discount terms |
| **VIN** | Vehicle Identification Number — unique 17-character identifier |
| **Plate Number** | Australian registration plate (e.g., VIC GLR A001) |
| **BYO** | Bring Your Own — customer registers their existing vehicle |
| **Demo Vehicle** | Vehicle used for test drives and demo purposes |
| **Pool Vehicle** | Vehicle in the hire fleet, cycles between available and hired |

## 3. User Flow Diagrams

### 3.1 Vehicle Discovery Flow

```
[App Launch] → [Home Dashboard]
                    │
                    ├── [Browse Vehicles]
                    │        │
                    │        ├── Apply Filters (brand, price, range, drivetrain)
                    │        │        │
                    │        │        └── [Filtered Results List]
                    │        │                       │
                    │        │                       └── Tap Vehicle Card
                    │        │
                    │        └── [Search Bar]
                    │                       │
                    │                       └── [Semantic Search Results]
                    │
                    └── [Vehicle Detail Page]
                                 │
                                 ├── View Specs, Gallery, Availability
                                 ├── Configure Vehicle (if available)
                                 └── [Book Test Drive]  → [Booking Flow]
                                     [Add to Wishlist]
```

### 3.2 Authentication & Onboarding Flow

```
[App Launch] → [Is user authenticated?]
                    │
                    ├── No → [Sign In / Sign Up]
                    │              │
                    │              ├── Sign Up: Enter email/phone → Receive OTP
                    │              │                              → Verify OTP
                    │              │                              → Set password
                    │              │                              → [Home Dashboard]
                    │              │
                    │              └── Sign In: Enter email/phone → Receive OTP
                    │                                               → Verify OTP
                    │                                               → [Home Dashboard]
                    │
                    └── Yes → [Home Dashboard]
```

### 3.3 Test Drive Booking Flow

```
[Vehicle Detail] or [Browse] → [Book Test Drive Button]
                                      │
                                      → [Select Vehicle] (pre-filled from context)
                                      │
                                      → [Select Dealership Location]
                                      │      ├── Show map with dealership pins
                                      │      └── Show distance from user
                                      │
                                      → [Select Date & Time Slot]
                                      │      ├── Calendar view with available slots
                                      │      └── Color-coded: green=available, red=booked
                                      │
                                      → [Confirm Booking Details]
                                      │      ├── Review vehicle, location, time
                                      │      └── Enter contact phone (if not saved)
                                      │
                                      → [Booking Confirmed]
                                      │      ├── Display QR code
                                      │      ├── Show vehicle details
                                      │      ├── Add to calendar option
                                      │      └── Map directions link
                                      │
                                      → [Push Notification] sent
```

### 3.4 Vehicle Configuration & Purchase Flow

```
[Vehicle Detail] → [Configure] Button
                       │
                       → [Step 1: Select Trim Level]
                       │
                       → [Step 2: Exterior Color]
                       │
                       → [Step 3: Interior Color & Material]
                       │
                       → [Step 4: Wheels]
                       │
                       → [Step 5: Technology Packages]
                       │
                       → [Step 6: Review Configuration & Price]
                       │      ├── Configuration summary
                       │      └── On-road price breakdown
                       │
                       → [Step 7: Finance/Lease Selection]
                       │      ├── Finance calculator (down payment, term, monthly)
                       │      └── Buy vs Lease comparison
                       │
                       → [Step 8: Secure Deposit Payment]
                       │      ├── Payment form (Stripe/PayPal)
                       │      └── Payment confirmation
                       │
                       → [Order Created]
                       │      ├── Order number generated
                       │      └── Redirect to Order Status tracker
```

### 3.5 Order Tracking & Delivery Flow

```
[Orders Tab] → [Active Order Details]
                    │
                    └── [Timeline View]
                            ├── Received ✓
                            ├── Approved ✓
                            ├── In Production ⟳ (current)
                            ├── In Transit ⏳
                            ├── Arrived at Dealership ⏳
                            └── Ready for Delivery ⏳
                                      │
                                      → [Delivery Scheduled?]
                                      │      ├── No → [Schedule Delivery]
                                      │      │              → Pick date/time
                                      │      │              → Confirm
                                      │      │
                                      │      └── Yes → Show scheduled date/time
                                      │
                                      → [Digital Handover] (on delivery day)
                                              ├── E-sign delivery documents
                                              ├── Review handover checklist
                                              ├── Download document pack
                                              └── [Delivery Complete]
```

### 3.6 Service & Maintenance Flow

```
[Profile] or [Home Dashboard] → [Service & Maintenance]
                                      │
                                      ├── [Service History]
                                      │       └── Timeline of past services
                                      │
                                      ├── [Book Service]
                                      │       ├── Select service type (routine, recall, repair)
                                      │       ├── Select location
                                      │       ├── Select date/time
                                      │       └── Confirm → [Booking Confirmed]
                                      │
                                      ├── [Upcoming Reminders]
                                      │       └── List of upcoming service/warranty dates
                                      │
                                      └── [Warranty Info]
                                              └── Coverage details, terms, claims
```

---

## 4. Screen Inventory

### 4.1 Authentication Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| A1 | Sign In | Email/phone entry + OTP verification | ✅ |
| A2 | Sign Up | New account registration + OTP verification | ✅ |
| A3 | Forgot Password / Reset | Password recovery via OTP | ✅ |

### 4.2 Main Navigation Screens (Bottom Tab Bar)

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| M1 | **Home Dashboard** | Promo banner, quick actions, featured vehicles, recent activity | ✅ |
| M2 | **Browse** | Vehicle catalog with search, filters, sort | ✅ |
| M3 | **Bookings** | Upcoming test drives & service appointments, booking history | ✅ |
| M4 | **Orders** | Active and past orders with status timeline | ✅ |
| M5 | **Profile** | Account settings, documents, service history, warranty info | ✅ |

### 4.3 Vehicle & Discovery Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| V1 | Vehicle List / Grid | Filtered search results with vehicle cards | ✅ |
| V2 | Vehicle Detail | Full specs, gallery, availability, CTA buttons | ✅ |
| V3 | Vehicle Comparison | Side-by-side comparison of up to 3 vehicles | Phase 2 |
| V4 | Vehicle Configurator | Interactive trim/color/options selection with live pricing | ✅ |
| V5 | Search Results | Semantic/AI-powered search results page | Phase 2 |

### 4.4 Booking Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| B1 | Test Drive Booking | Select vehicle, location, date/time | ✅ |
| B2 | Booking Confirmation | QR code, details, calendar add, map link | ✅ |
| B3 | My Bookings | List of upcoming and past bookings | ✅ |
| B4 | Booking Detail | Single booking details with reschedule/cancel options | ✅ |
| B5 | Service Booking | Select service type, location, date/time | ✅ |
| B6 | Location Selector | Map view of dealership/service centers | ✅ |

### 4.5 Purchase & Order Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| P1 | Order List | List of all orders (active + archived) | ✅ |
| P2 | Order Detail / Timeline | Milestone tracker with status updates | ✅ |
| P3 | Finance Calculator | Buy vs lease, monthly payment estimator | ✅ |
| P4 | Payment Screen | Secure deposit/full payment form | ✅ |
| P5 | Payment Confirmation | Receipt, order number, next steps | ✅ |

### 4.6 Delivery & Handover Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| D1 | Delivery Notification | Push/SMS-influenced arrival alert screen | ✅ |
| D2 | Delivery Scheduling | Pick delivery date/time slot | ✅ |
| D3 | Digital Handover | E-signature, document review, checklist | ✅ |
| D4 | Document Pack Viewer | PDF viewer/downloader for delivery documents | ✅ |

### 4.7 Post-Purchase & Service Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| S1 | Service History | Timeline of all past services | ✅ |
| S2 | Warranty Info | Coverage details, terms, claims info | ✅ |
| S3 | Reminders | Upcoming service/warranty/alerts list | ✅ |
| S4 | Service Request Detail | Individual service request tracking | Phase 2 |

### 4.8 Profile & Settings Screens

| # | Screen | Purpose | MVP? |
|---|--------|---------|------|
| T1 | Profile Overview | User info, quick links, saved vehicles | ✅ |
| T2 | Account Settings | Edit contact, notification preferences, password | ✅ |
| T3 | My Documents | Accessible PDF documents (orders, service, warranty) | ✅ |
| T4 | Wishlist / Saved Vehicles | Saved vehicles list | Phase 2 |
| T5 | Help & Support | FAQs, contact info, feedback form | Phase 2 |

**Total MVP Screens: ~28 | Total Phase 2 Screens: ~5**

---

## 5. Acceptance Criteria per Feature

### 5.1 Feature: Vehicle Exploration & Discovery (US-1)

| ID | Criterion |
|----|-----------|
| AC-1.1 | User can browse all available vehicle models in a grid/list view with at least 4 cars per row on desktop, 2 per row on mobile. |
| AC-1.2 | Each vehicle card displays: thumbnail image, model name, range (km), drivetrain (FWD/RWD/AWD), charging speed (kW), and starting price. |
| AC-1.3 | User can filter vehicles by: brand, price range, body type, battery range, drivetrain. Filters are combinable. |
| AC-1.4 | Tapping/clicking a vehicle card navigates to the Vehicle Detail screen within 500ms. |
| AC-1.5 | Vehicle Detail screen shows: full image gallery (swipeable), complete specification table, color options, current availability status, and CTA buttons (Book Test Drive, Configure). |
| AC-1.6 | Availability status displays one of: "In Stock — [Location]", "Available in [X] weeks", or "Pre-order Now". |
| AC-1.7 | Pricing displayed is the full on-road price including taxes; a breakdown is available via tap. |

### 5.2 Feature: Self-Service Portal & Account (US-2)

| ID | Criterion |
|----|-----------|
| AC-2.1 | User can register with email or phone number and verify identity via 6-digit OTP code delivered within 30 seconds. |
| AC-2.2 | OTP expires after 5 minutes; max 3 retry attempts before cooldown. |
| AC-2.3 | Upon successful login, user is redirected to the Home Dashboard. |
| AC-2.4 | Home Dashboard displays: promo banner, quick action buttons (Book Test Drive, Track Order, Book Service), featured vehicles, and recent notifications. |
| AC-2.5 | User can download documents (PDF) related to their orders and bookings from the Documents section. |
| AC-2.6 | User can edit profile fields: full name, phone number, email, notification preferences. |
| AC-2.7 | Session persists across app close/reopen for 30 days; auto-logout after 30 days of inactivity. |

### 5.3 Feature: Test Drive Booking & Management (US-3)

| ID | Criterion |
|----|-----------|
| AC-3.1 | User can initiate test drive booking from Vehicle Detail screen or Browse screen. |
| AC-3.2 | Booking form captures: vehicle (pre-filled), dealership location, preferred date, preferred time slot. |
| AC-3.3 | Time slot grid prevents double-booking; already-booked slots are visually greyed out. |
| AC-3.4 | Upon submission, user receives instant on-screen confirmation with: booking reference code, vehicle details, date/time, dealership address, QR code. |
| AC-3.5 | Confirmation pushes a notification (push + email) within 60 seconds. |
| AC-3.6 | User can view all bookings in the Bookings tab, sorted by upcoming date. |
| AC-3.7 | User can cancel a booking up to 24 hours before the scheduled time; cancellations after 24 hours require manual dealer approval. |
| AC-3.8 | User can reschedule a booking by selecting a new available slot. |

### 5.4 Feature: Configuration, Purchase & Order Tracking (US-4)

| ID | Criterion |
|----|-----------|
| AC-4.1 | Configurator displays all available options for the selected model: trim levels, exterior colors, interior colors, wheel options, technology packages. |
| AC-4.2 | Price updates in real-time as options are selected; total price always visible at screen bottom. |
| AC-4.3 | Finance calculator accepts: down payment amount, loan/lease term (months), and displays estimated monthly payment. |
| AC-4.4 | User can toggle between "Buy" and "Lease" modes to compare monthly costs side-by-side. |
| AC-4.5 | Deposit payment integrates with a PCI-compliant payment gateway (Stripe or equivalent). |
| AC-4.6 | Payment screen displays: total due, payment method options (credit card, debit card), secure payment badge. |
| AC-4.7 | After successful payment, user receives: order number, payment receipt, and redirect to Order Status timeline. |
| AC-4.8 | Order status timeline shows milestones: Received → Approved → In Production → In Transit → Arrived → Ready for Delivery. |
| AC-4.9 | Each milestone displays: status label, date/time, and brief description. |

### 5.5 Feature: Delivery Notification & Digital Handover (US-5)

| ID | Criterion |
|----|-----------|
| AC-5.1 | User receives automated push notification, SMS, and email when vehicle status changes to "Arrived at Dealership". |
| AC-5.2 | Notification includes: vehicle details, dealership address, and "Schedule Delivery" CTA. |
| AC-5.3 | Delivery scheduling shows available date/time slots at the assigned dealership. |
| AC-5.4 | Digital Handover screen presents: delivery documents for review, e-signature pad (touch/drag), and handover checklist. |
| AC-5.5 | E-signed documents are stored and accessible in the user's Document Pack. |
| AC-5.6 | Document Pack includes: Certificate of Registration, Warranty Certificate, Owner's Manual, Service Booklet, Keys Receipt — all downloadable as PDF. |
| AC-5.7 | Handover checklist items are marked complete by the customer; all items must be checked before handover is finalized. |

### 5.6 Feature: Vehicle Service & Maintenance (US-6)

| ID | Criterion |
|----|-----------|
| AC-6.1 | Service History displays a chronological timeline of all past services: date, dealer, service type, description, cost. |
| AC-6.2 | User can book a maintenance appointment by selecting: service type, dealership location, preferred date/time. |
| AC-6.3 | Service booking follows the same conflict-validation pattern as test drive booking (no double-booking). |
| AC-6.4 | Proactive reminders are sent: 14 days before service is due, 30 days before warranty expiry, and immediately upon recall notices. |
| AC-6.5 | Warranty Info screen displays: coverage start/end dates, covered items, exclusions, and claims process steps. |
| AC-6.6 | Service reminders are delivered via push notification and email. |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Requirement | Target |
|-------------|--------|
| Initial page load (Home Dashboard) | < 2 seconds on 4G, < 1 second on Wi-Fi |
| API response time (p95) | < 300ms for read operations, < 1 second for write operations |
| Time-to-Interactive (TTI) | < 3 seconds on mobile devices |
| Image loading | Lazy-loaded, WebP format, < 100KB per image |
| Concurrent users (MVP) | Support ≥ 1,000 concurrent users |
| Search response time | < 500ms for catalog search, < 1 second for semantic/vector search |

### 6.2 Security

| Requirement | Specification |
|-------------|---------------|
| Authentication | Email/phone + OTP; JWT-based session tokens (access token: 15 min, refresh token: 30 days) |
| Password storage | Argon2id or bcrypt with salt; never store plaintext |
| Data in transit | TLS 1.3 enforced across all endpoints |
| Data at rest | AES-256 encryption for PII in PostgreSQL; encrypted backups |
| Payment security | PCI DSS Level 1 compliance via Stripe/PayPal integration; no card data stored locally |
| E-signatures | Legally binding e-signatures compliant with Australian ESIGN legislation |
| GDPR/CCPA | Data export (GET) and data deletion (DELETE) endpoints per user account |
| Rate limiting | API gateway-level rate limiting: 60 requests/minute for anonymous, 200 requests/minute for authenticated |
| Input validation | All inputs validated server-side; OWASP Top 10 protections implemented |
| CSP Headers | Strict Content Security Policy enforced on all pages |

### 6.3 Accessibility

| Requirement | Specification |
|-------------|---------------|
| WCAG Compliance | WCAG 2.1 Level AA minimum across all screens |
| Color Contrast | Minimum 4.5:1 for normal text, 3:1 for large text and UI components |
| Screen Reader | Full ARIA labels on interactive elements; semantic HTML structure |
| Keyboard Navigation | All functionality operable via keyboard (Tab, Enter, Space, Escape) |
| Font Scaling | Content readable at 200% browser zoom |
| Touch Targets | Minimum 48×48px touch targets on all interactive elements |
| Reduced Motion | Respects OS-level prefers-reduced-motion setting |

### 6.4 Reliability & Availability

| Requirement | Target |
|-------------|--------|
| Uptime SLA | 99.9% monthly availability |
| Error rate | < 0.1% of API requests |
| Data backup | Daily automated backups; RPO ≤ 24 hours, RTO ≤ 4 hours |
| Disaster recovery | Failover to secondary availability zone within Melbourne DC |

### 6.5 Compatibility

| Requirement | Specification |
|-------------|---------------|
| Mobile browsers | Chrome (latest 2 versions), Safari (latest 2 versions), Firefox (latest 2 versions) |
| Desktop browsers | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| Mobile OS | iOS 15+, Android 10+ |
| Responsive breakpoints | Mobile (< 768px), Tablet (768–1024px), Desktop (> 1024px) |
| PWA support | Installable on iOS and Android with offline shell |

### 6.6 Observability

| Requirement | Specification |
|-------------|---------------|
| Application logging | Structured JSON logs to centralized log aggregation |
| Error tracking | Sentry or equivalent for client-side and server-side error capture |
| Performance monitoring | Real User Monitoring (RUM) for frontend, APM for backend |
| Business analytics | Event tracking for key user actions (booking, purchase, service) |

---

## 7. Out of Scope for MVP

The following features are explicitly excluded from the MVP scope and deferred to future phases:

| Feature | Rationale |
|---------|-----------|
| **Native mobile apps (iOS/Android)** | MVP delivered as responsive web app + PWA; native wrappers in Phase 2 |
| **AI-powered semantic search** | Qdrant vector search deferred until after core catalog is stable |
| **Vehicle comparison tool** | Low priority vs core purchasing flow |
| **Trade-in valuation** | Requires integration with valuation APIs; Phase 2 |
| **Emergency roadside assist** | Requires telephony/SOS infrastructure; Phase 2 |
| **Push notification service** | Email/SMS only for MVP; push notifications in Phase 2 |
| **In-app chat / live chat support** | External support channel sufficient for MVP |
| **Loyalty / rewards program** | ✅ IMPLEMENTED — 5-tier system with points and rewards (US-8) |
| **Referral program** | Post-launch growth feature |
| **Multi-language support** | English only for MVP (Australian market) |
| **Dealer staff admin portal** | Managed via separate internal system (GloryEV_EP1) |
| **In-app payments beyond deposits** | Full payment at dealership for MVP |
| **Vehicle telemetry integration** | Requires OEM API partnership; future phase |
| **Social sharing / UGC** | Growth feature, not core functionality |
| **Apple Pay / Google Pay** | Standard card payments via Stripe for MVP |

---

## 8. Prioritized Feature List: MVP vs Phase 2

### 8.1 MVP (Must Have — Launch)

**Priority: P0 — Core Experience**

| # | Feature | User Story | Effort |
|---|---------|------------|--------|
| 1 | Vehicle Catalog Browsing (search, filters, vehicle cards) | US-1 | Medium |
| 2 | Vehicle Detail Page (specs, gallery, availability, pricing) | US-1 | Medium |
| 3 | User Registration & Authentication (email + OTP, JWT) | US-2 | Medium |
| 4 | Customer Dashboard (Home screen with quick actions, featured vehicles) | US-2 | Medium |
| 5 | Test Drive Booking (calendar, location, confirmation with QR) | US-3 | High |
| 6 | Booking Management (view, cancel, reschedule bookings) | US-3 | Medium |
| 7 | Vehicle Configurator (trim, color, options, live pricing) | US-4 | High |
| 8 | Finance/Lease Calculator (buy vs lease, monthly estimator) | US-4 | Medium |
| 9 | Secure Deposit Payment (Stripe integration) | US-4 | High |
| 10 | Order Status Timeline (milestone tracker) | US-4 | Medium |
| 11 | Delivery Scheduling & Notification | US-5 | Medium |
| 12 | Digital Handover (e-signature, checklist, document pack) | US-5 | High |
| 13 | Service History View | US-6 | Low |
| 14 | Service Booking | US-6 | Medium |
| 15 | Warranty Information Display | US-6 | Low |
| 16 | Profile & Account Management | US-2 | Low |
| 17 | Document Access & Download | US-2 | Medium |
| 18 | Email Notifications (booking confirmations, order updates, reminders) | US-3, US-4, US-5, US-6 | Medium |

**MVP Timeline Estimate: 12–16 weeks**

### 8.2 Phase 2 (Should Have — 1–2 Quarters Post-Launch)

| # | Feature | User Story | Effort |
|---|---------|------------|--------|
| 1 | AI-Powered Semantic Search (Qdrant vector search) | US-1 | High |
| 2 | Push Notifications (FCM/APNs) | US-3, US-4, US-5 | Medium |
| 3 | Proactive Service Reminders (automated scheduling) | US-6 | Medium |
| 4 | Native iOS App (React Native / Flutter wrapper) | US-2 | High |
| 5 | Native Android App | US-2 | High |
| 6 | Vehicle Comparison Tool (side-by-side) | US-1 | Medium |
| 7 | Trade-In Valuation | US-4 | Medium |
| 8 | Wishlist / Saved Vehicles | US-1 | Low |
| 9 | In-App Chat / Live Support | US-2 | Medium |
| 10 | Apple Pay / Google Pay | US-4 | Medium |
| 11 | Emergency Roadside Assist | US-6 | High |
| 12 | Loyalty & Referral Program | — | Medium |
| 13 | Multi-Language Support | — | Medium |
| 14 | Vehicle Telemetry Dashboard (battery health, charging stats) | US-6 | High |
| 15 | Advanced Analytics & Personalization | US-1 | High |

### 8.3 Phase 3 (Nice to Have — 6+ Months Post-Launch)

| # | Feature | Notes |
|---|---------|-------|
| 1 | Social sharing & user-generated content | Community features |
| 2 | EV charging station locator | Map integration with charge points |
| 3 | Over-the-air (OTA) update notifications | OEM integration |
| 4 | In-app insurance management | Insurance partner integration |
| 5 | Vehicle marketplace / resale | Secondary market platform |

---

## 9. Technical Constraints & Stack

### 9.1 Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Cloud Hosting** | Azure Australia (Melbourne DC) | Region: `australia-southeast` |
| **Frontend** | Python FastAPI + Jinja2 templates | Server-side rendered, mobile-first responsive |
| **API Gateway** | Azure API Gateway (or open-source alternative: Kong/Tyk) | Rate limiting, auth, routing |
| **Database** | PostgreSQL 15+ | Primary relational store; Azure Database for PostgreSQL |
| **Vector Datastore** | Qdrant | Semantic search, AI recommendations |
| **Deployment** | Docker containers | Containerized microservices |
| **Design System** | Open Design Framework | https://github.com/nexu-io/open-design |
| **Payment** | Stripe (or equivalent PCI-compliant gateway) | Deposits and payments |
| **Email** | SendGrid / Azure Communication Services | Transactional emails |
| **SMS** | Twilio / Azure Communication Services | OTP and notifications |

### 9.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │  Mobile    │  │  Desktop  │  │   Tablet   │  (PWA)      │
│  │  Browser   │  │  Browser  │  │  Browser   │              │
│  └─────┬──────┘  └─────┬─────┘  └─────┬──────┘              │
│        │              │              │                      │
└────────┼──────────────┼──────────────┼──────────────────────┘
         │              │              │   HTTPS / TLS 1.3
         └──────────────┴──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │   API Gateway (Azure / Kong)  │
         │   • Rate limiting             │
         │   • Auth (JWT validation)    │
         │   • Request routing           │
         └──────────────┬───────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
┌───┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
│ Customer  │    │ Vehicle     │    │ Booking     │
│ Portal    │    │ Catalog     │    │ Service     │
│ Microsvc  │    │ Microsvc    │    │ Microsvc    │
│ (FastAPI) │    │ (FastAPI)   │    │ (FastAPI)   │
└─────┬─────┘    └──────┬──────┘    └──────┬──────┘
      │                 │                   │
      │          ┌──────┴──────┐            │
      │          │  Order &    │            │
      │          │  Payment    │            │
      │          │  Microsvc   │            │
      │          │  (FastAPI)  │            │
      │          └──────┬──────┘            │
      │                 │                   │
      └────────┬────────┴──────────┬────────┘
               │                   │
    ┌──────────┴──────────┐  ┌────┴──────────┐
    │   PostgreSQL        │  │   Qdrant      │
    │   (Azure DB)        │  │   (Vector DB)  │
    │   • Orders          │  │   • Semantic   │
    │   • Bookings        │  │     search     │
    │   • Users           │  │   • Recs       │
    │   • Documents       │  └────────────────┘
    │   • Leads           │
    └─────────────────────┘
```

### 9.3 Design System & Branding

| Property | Value |
|----------|-------|
| **Design Framework** | Open Design — https://github.com/nexu-io/open-design |
| **Primary Brand Color** | `#2E7D32` (Forest Green) |
| **Mobile Frame Max Width** | 390px |
| **Bottom Navigation** | Home, Browse, Bookings, Orders, Profile |
| **Typography** | To be defined by UI/UX team (Open Design defaults) |
| **Icon Style** | Material Icons or Open Design icon set |

### 9.4 Data Privacy & Compliance

- **Privacy:** Compliance with Australian Privacy Principles (APP) under the Privacy Act 1988.
- **Data Residency:** All customer data stored within Azure Australia (Melbourne DC).
- **Consent:** Explicit opt-in for notifications and marketing communications.
- **Retention:** Customer data retained for 7 years post-account closure (legal requirement); anonymized after.

---

## 10. Appendix: Glossary & References

### 10.1 Glossary

| Term | Definition |
|------|-----------|
| **DIN** | Drive Information Notification — legal delivery document in Australia |
| **OTP** | One-Time Password — 6-digit verification code sent via SMS or email |
| **PWA** | Progressive Web App — web app with native-like install and offline capabilities |
| **JWT** | JSON Web Token — stateless authentication token |
| **RPO** | Recovery Point Objective — maximum tolerable data loss measured in time |
| **RTO** | Recovery Time Objective — maximum tolerable downtime measured in time |
| **FCM** | Firebase Cloud Messaging — Android push notification service |
| **APNs** | Apple Push Notification service — iOS push notification service |
| **CSAT** | Customer Satisfaction Score |

### 10.2 References

| Document | Location |
|----------|----------|
| Raw Requirements (Obsidian) | Original source note |
| Open Design Framework | https://github.com/nexu-io/open-design |
| Sample UI Mockups | Existing HTML mockups in project workspace |
| GloryEV EP1 (Internal System) | `/home/terry/workspace/projects/GloryEV_EP1/` |
| Azure Australia Region Docs | https://azure.microsoft.com/en-au/global-infrastructure/regions/ |
| Stripe API Docs | https://stripe.com/docs/api |
| Qdrant Docs | https://qdrant.tech/documentation/ |
| FastAPI Docs | https://fastapi.tiangolo.com/ |

### 10.3 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-01 | Product Management | Initial PRD draft — Stage 1 of build pipeline |
| 1.1 | 2026-06-12 | Engineering | Added US-7 (Car Hiring), US-8 (Membership), US-9 (Customer Care) — features implemented beyond original MVP scope |

---

*End of PRD v1.0*
