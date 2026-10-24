# SwasthyaSetu Dropdown Bug Report (Task 1)

**Date:** 2026-10-24  
**Project:** SwasthyaSetu Platform (`D:\AWS`)  
**Target:** Doctor Clinical Safety Workspace (`frontend_portal/templates/doctor.html`, `frontend_portal/static/js/doctor.js`, `frontend_portal/static/js/components.js`)  
**Status:** Step 1 (Reproduction) & Step 2 (Suspect Audit) COMPLETE  

---

## 1. Executive Summary & Reproduction

Before applying any code changes, automated tests with Playwright reproduced the medicine search dropdown bug at both **1280px** (Desktop) and **360px** (Mobile) viewports.

### Reproduction Artifacts
- **Desktop (1280px):** `docs/screenshots/dropdown_reproduce_1280.png`
- **Mobile (360px):** `docs/screenshots/dropdown_reproduce_360.png`

### Observed Defects During Reproduction
1. **Data Contract Failure ("No medicines found"):**
   Typing `"aug"` in the medicine search input resulted in an empty result box displaying `"No medicines found."`, despite the catalog containing 253,973 indexed Indian medicines (including Augmentin 625 Duo Tablet).
   - **Root Cause:** Backend `/api/medicines-catalog?q=aug` returns `matches` and `results` arrays containing objects with `brand_name`, `generic_composition`, `unit_price`, etc. However, `doctor.js:701` inspected `data.medicines` (which is `undefined`), resulting in `items = []`.
2. **Layout & Anchoring Defect at 1280px:**
   - The input width is `406.9px`, but the dropdown results box rendered at `630px` width.
   - The dropdown container was positioned `absolute left-0 right-0 top-full` inside a parent `.form-group.relative` that contained **both** the search input and two adjacent action buttons ("Test Augmentin", "Test Aspirin"). This caused the dropdown to stretch across the sibling buttons and render directly on top of the next field ("Resolved Generic Composition / Salts"), causing visual label collisions.
3. **Catastrophic Failure at 360px Mobile Viewport:**
   - On a 360px mobile viewport, `.doctor-nav-rail` occupied 300px of fixed width, leaving only 60px for `.doctor-main-content`.
   - The search input was squished to `26px` width, and the absolute results box was squished to `10px` width at `x=300px` (completely off-screen and unreadable).
4. **Missing ARIA & Keyboard Navigation:**
   - The component was a plain HTML input without `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, or `aria-activedescendant`.
   - Up/Down arrow keys did not navigate options; pressing Enter caused unintended form submission; Escape did not dismiss the dropdown.
5. **Stacking Context & Clipping:**
   - Positioned absolutely inside scrolling parents, the dropdown was clipped by parent boundaries and lacked auto-flipping when rendered near the bottom of the viewport.

---

## 2. Suspect Audit & PASS / FAIL Matrix

| # | Suspect Description | Status | Evidence & Technical Assessment |
|---|---------------------|:------:|---------------------------------|
| **1** | **Parent clipping (overflow:hidden/auto or transform/filter)** | **FAIL** | `#section-prescriptions` sits inside `.doctor-main-content` which has `overflow-y: auto`. In modals or side panels, `overflow: hidden` clips an absolutely positioned list or restricts it to a sub-optimal stacking context. |
| **2** | **z-index lower than sticky header, panels, or modal overlays** | **FAIL** | Dropdown had `z-20`. The safety rail has `position: sticky; z-index: 30`, header controls have `z-30`, and modal overlays have `z-50`. Dropdown gets covered by modals and sticky sidebars. |
| **3** | **Native `<select>` or `<datalist>` unstyled/inconsistent** | **FAIL** | Medicine search used a raw un-styled `<div>`, while frequency, treatment duration, translator languages, occupation, and work-risk pickers used native unstyled `<select>` tags lacking rich two-line layouts. |
| **4** | **Positioned relative to wrong element / fails on scroll & resize** | **FAIL** | Anchored to `.form-group.relative` (wrapping input + 2 buttons), stretching to 630px instead of matching input width (406px). Fails to track input on scroll, window resize, or virtual keyboard appearance. |
| **5** | **Width smaller than input or long names truncated** | **FAIL** | At 360px viewport, width collapsed to 10px. Long medicine names ("Augmentin 625 Duo Tablet", "Atorvastatin Calcium 10mg") overflowed and clipped without wrapping. |
| **6** | **No max-height/scroll or thousands of rows unpaginated** | **FAIL** | Catalog contains 253,973 medicines. Backend default was 20, frontend requested 10, requirement specifies server-side search limited to 15 results with internal max-height scroll. |
| **7** | **Text and background color contrast in light/dark themes** | **FAIL** | `#med-search-results` lacked explicit background opacity tokens in dark mode, causing background text bleed-through and contrast issues. |
| **8** | **List closes on blur before click registers** | **FAIL** | Relied on click handlers without `pointerdown` / `mousedown` `preventDefault()`. Clicking an item caused the input to blur and dismiss the dropdown before selection completed. |
| **9** | **Race condition: slow responses arrive out of order** | **FAIL** | `doctor.js` used a plain `setTimeout` debounce with no `AbortController` or sequence counter. A slow query for `"au"` could overwrite a faster response for `"augmentin"`. |
| **10** | **Keyboard and screen-reader behavior missing/broken** | **FAIL** | No ARIA combobox semantics (`role="combobox"`, `listbox`, `option`, `aria-activedescendant`). No Arrow Up/Down navigation, Enter selection, Escape dismissal, or Home/End scrolling. |

---

## 3. The Solution: Unified ARIA Combobox Component

To permanently resolve all 10 issues, we implement **ONE reusable ARIA Combobox component** (`Combobox` in `frontend_portal/static/js/components.js`) used for:
1. **Medicine Search** (server-side, 15 results, debounced 200ms)
2. **Frequency Picker** (client-side options)
3. **Treatment Duration Picker** (quick picks 3/5/7/14/30 days + custom)
4. **BhashaSehat Translator Languages**
5. **KaamSuraksha Occupation & Work-Risk Symptoms**
6. **ASHA Worker Picker**

### Key Architecture:
- **Body Portal:** Renders `<div role="listbox">` attached directly to `document.body` with `position: fixed` and `z-index: 9999`.
- **Bounding Box Computation:** Positions dynamically via `input.getBoundingClientRect()`, repositioning on `scroll`, `resize`, and `visualViewport` changes.
- **Auto-Flipping:** If distance between input bottom and viewport bottom is < 260px, flips upward automatically.
- **Two-Line Rich Option Items:**
  - Line 1: Bold brand name with matched substring highlighted (`<mark>`).
  - Line 2: Muted text with generic salt, dosage form, pack size, price (₹), manufacturer, and a "Discontinued" pill if applicable.
  - Option item min-height $\ge 44\text{px}$ for touch accessibility; text wraps cleanly without truncation.
- **States:** Loading skeleton rows, Empty state ("No medicine found. Check the spelling."), Hint state ("Type at least 2 characters..."), and Error state with "Retry" action.
- **Robust Event Handling:** Selection on `pointerdown` with `preventDefault()` to prevent blur race conditions.
- **AbortController:** Cancels in-flight HTTP requests when query changes.
- **ARIA & Keyboard Support:** Arrow Up/Down, Enter, Escape, Tab, Home/End, updating `aria-activedescendant` and auto-scrolling active item into view.
- **Responsive Layout:** Doctor workspace flex layout updated with `@media (max-width: 768px)` so navigation collapses/adapts and main workspace is 100% width.
