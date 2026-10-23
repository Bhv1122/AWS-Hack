---
name: Clinical Clarity
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3d4947'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#006947'
  on-tertiary: '#ffffff'
  tertiary-container: '#00855b'
  on-tertiary-container: '#f5fff6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Inter
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1rem
  gutter-tablet: 1.5rem
  margin-tablet: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system establishes an empathetic, clinically rigorous, and highly accessible interface tailored for mobile-first patient adherence, medication tracking, and provider collaboration. 

The emotional signature is calming, authoritative, and frictionless. Patients handling chronic treatment regimens or acute prescriptions are often navigating cognitive overload, stress, or mild visual/motor impairment. The UI rejects cold, intimidating hospital minimalism in favor of a warm, human-centered modern clinical aesthetic: generous spacing, deliberate chromatic signifiers, and crystal-clear typographic hierarchy.

Key style pillars:
- **Calm Authority:** Grounded in clinical teals and trust-inducing blues that reduce patient anxiety.
- **Immediate Legibility:** High-contrast tokens, oversize baseline touch targets (minimum 48x48pt), and distinct semantic alert colors.
- **Physical Metaphor:** Subtle pill-shaped geometries and soft, tactile surface elevation that echo tangible pharmaceutical design without visual clutter.

## Colors

The palette is engineered around instant semantic recognition and calm optical balance against a clinical soft slate canvas.

- **Primary (`#0D9488` - Medical Teal):** The foundational brand color used for core navigation, primary medication actions, confirmed states, and restorative clinical touchpoints.
- **Secondary (`#2563EB` - Trust Blue):** Reserved for technical workflows, clinical record synchronizations, active interactive links, and provider verification indicators.
- **Tertiary (`#10B981` - Emerald Green):** Strictly denotes safe conditions, successful adherence ("Taken"), verified refill status, and non-conflicting drug regimes.
- **Warning / Pending (`#F59E0B` - Amber):** Highlights upcoming dosage windows, impending expiration dates, or moderate caution notices.
- **Critical Alert (`#EF4444` - Coral Red):** Exclusively deployed for critical drug-drug interactions, missed doses past grace windows, and vital allergy warnings.
- **Canvas & Surfaces:** Baseline canvas sits on `#F8FAFC` (Slate 50), contrasting with `#FFFFFF` pure white elevated cards to define clear actionable boundaries. Text scales from deep slate `#0F172A` down to `#64748B` for secondary instructions, consistently preserving a minimum 4.5:1 WCAG AA contrast ratio.

## Typography

The typographic pairing balances approachable geometric warmth with clinical objectivity.

- **Headlines (Plus Jakarta Sans):** Introduces friendly, wide apertures and gentle terminal curves that make dosage titling, greetings, and screen banners welcoming rather than clinical and detached.
- **Body & Data (Inter):** Leverages tall x-heights, neutral letterforms, and unambiguous numeral glyphs (crucial for distinguishing milligrams, units, and schedule intervals like "0" vs "O" and "1" vs "l").
- **Dynamic Type & Scaling:** Font sizes scale down slightly on narrow mobile viewports via designated mobile tokens while upholding generous line-heights to support users increasing accessibility text zoom levels on mobile operating systems.

## Layout & Spacing

The layout philosophy follows a fluid 4-column system for mobile viewports, stepping up to an 8-column layout on tablet screens with centered maximum readable widths.

- **Touch Ergonomics:** Component containers strictly adhere to an 8pt base grid. Primary action areas, timeline tracks, and medication logs align within the thumbs' natural sweep zone at the bottom two-thirds of the viewport.
- **Vertical Spacing:** Generous whitespace around medication schedules prevents fatal tap errors between adjacent dosages. Elements with distinct clinical intents (e.g., "Confirm Dose" vs. "Snooze/Skip") require at least `space-md` separation.
- **Margins & Gutters:** Base mobile experiences utilize `1rem` (16px) margins to preserve edge-to-edge content density without crowding physical bezel limits.

## Elevation & Depth

Visual hierarchy uses subtle clinical shadows layered on pure white card surfaces over the `#F8FAFC` foundation.

- **Canvas (Level 0):** Flat background in soft slate (`#F8FAFC`).
- **Elevated Card (Level 1):** Solid white (`#FFFFFF`) backed by a diffused clinical shadow: `0px 2px 8px -2px rgba(15, 23, 42, 0.06), 0px 1px 3px 0px rgba(15, 23, 42, 0.04)`. Outlines are reinforced by a hairline low-contrast boundary (`border: 1px solid #E2E8F0`) to ensure contrast against ambient light.
- **Floating / Active Sheets & Modals (Level 2):** Applied to drug-drug interaction warnings and dose administration action drawers: `0px 12px 24px -4px rgba(15, 23, 42, 0.12), 0px 4px 8px -2px rgba(15, 23, 42, 0.06)`.
- **Alert Elevation:** Severe allergy or critical interaction banners elevate above the card layer with a tinted perimeter stroke (`1.5px solid #EF4444`) accompanied by an ambient Coral Red glow (`rgba(239, 68, 68, 0.12)`).

## Shapes

The design system adopts roundedness level `2` (0.5rem / 8px baseline radius), transitioning to pill shapes (`rounded-full`) for high-intent status controls and iconography.

- **Cards & Sheets:** Base corner radius is `0.75rem` (12px) to `1rem` (16px) (`rounded-lg` to `rounded-xl`), offering a soft, protective feel without sacrificing internal content area.
- **Capsule / Pill Metaphor:** Status tags, dose completion toggles, dose chips, and adherence progress bars make direct visual reference to medicinal capsules using continuous curvature (`9999px` radius).
- **Controls & Inputs:** Input text boxes, dropdowns, and button containers use `0.5rem` (8px) corners to preserve visual structure while remaining soft to the eye.

## Components

### Buttons
- **Primary Action (e.g., "Log Dose Taken"):** Filled with Medical Teal (`#0D9488`), white text, 48px minimum height, pill-shaped (`9999px`) or `rounded-lg`. High-emphasis tactile feedback.
- **Secondary Action (e.g., "Snooze 15m"):** Pure white fill, 1.5px Trust Blue (`#2563EB`) stroke, Trust Blue text.
- **Critical Action (e.g., "Report Severe Reaction"):** Subtle Coral Red wash background (`#FEF2F2`) with Coral Red (`#EF4444`) typography and border.

### Badges & Chips
- **Dosage Time Chips:** Pill-shaped, light slate background (`#F1F5F9`) with `#334155` text. Active or selected chips shift to solid Medical Teal with white text.
- **Status Badges:**
  - *Taken / Safe:* Emerald Green tint (`#ECFDF5`), `#065F46` label, paired with a checkmark icon.
  - *Upcoming / Due:* Amber tint (`#FFFBEB`), `#92400E` label, clock indicator.
  - *Critical Interaction / Allergy:* Coral Red tint (`#FEF2F2`), `#991B1B` label, bold warning octagon icon.

### Cards
- **Medication Schedule Card:** Pure white background, `rounded-xl`, subtle border (`#E2E8F0`). Houses pill iconography, trade/generic name, dosage strength, and direct single-tap confirmation targets.
- **Interaction Banner Card:** High-contrast layout with a 4px left-border accent matching the alert level (Emerald, Amber, or Coral Red).

### Lists & Dose Timelines
- Connected vertical timeline with node indicators showing chronological medication events (Morning, Afternoon, Evening, Bedtime). Nodes reflect status color tokens with completed items shifting to solid Emerald Green.

### Inputs & Selectors
- Form elements maintain a 48px target height with 16px horizontal internal padding. Resting borders use `#CBD5E1`, focusing to Trust Blue (`#2563EB`) with a 3px ring (`rgba(37, 99, 235, 0.15)`).

### Iconography
- Distinct 24x24pt line icons featuring pharmaceutical and anatomy metaphors: capsules, round tablets, liquid drops, inhalers, and shield checkmarks. Stroke width is fixed at 2px with rounded end-caps.