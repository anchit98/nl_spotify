---
name: Premium Insight Narrative
colors:
  surface: '#131314'
  surface-dim: '#131314'
  surface-bright: '#3a393a'
  surface-container-lowest: '#0e0e0f'
  surface-container-low: '#1c1b1c'
  surface-container: '#201f20'
  surface-container-high: '#2a2a2b'
  surface-container-highest: '#353436'
  on-surface: '#e5e2e3'
  on-surface-variant: '#bccbb9'
  inverse-surface: '#e5e2e3'
  inverse-on-surface: '#313031'
  outline: '#869585'
  outline-variant: '#3d4a3d'
  surface-tint: '#53e076'
  primary: '#53e076'
  on-primary: '#003914'
  primary-container: '#1db954'
  on-primary-container: '#004118'
  inverse-primary: '#006e2d'
  secondary: '#ddfcff'
  on-secondary: '#00363a'
  secondary-container: '#00f1fe'
  on-secondary-container: '#006a70'
  tertiary: '#ffb3b3'
  on-tertiary: '#680114'
  tertiary-container: '#ff767b'
  on-tertiary-container: '#730a1b'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#72fe8f'
  primary-fixed-dim: '#53e076'
  on-primary-fixed: '#002108'
  on-primary-fixed-variant: '#005320'
  secondary-fixed: '#74f5ff'
  secondary-fixed-dim: '#00dbe7'
  on-secondary-fixed: '#002022'
  on-secondary-fixed-variant: '#004f54'
  tertiary-fixed: '#ffdad9'
  tertiary-fixed-dim: '#ffb3b3'
  on-tertiary-fixed: '#400009'
  on-tertiary-fixed-variant: '#881d28'
  background: '#131314'
  on-background: '#e5e2e3'
  surface-variant: '#353436'
  surface-low: '#1C1C1E'
  surface-high: '#2C2C2E'
  border-subtle: rgba(255, 255, 255, 0.08)
  text-muted: '#8E8E93'
  status-warning: '#FFB020'
  status-error: '#FF5252'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.3'
  theme-sentence:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.5'
    letterSpacing: -0.01em
  body-main:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  metadata:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
  card-gap: 16px
---

## Brand & Style

The design system is engineered for high-density data synthesis, specifically tailored for internal analytics and executive decision-making. It eschews the playful, rounded energy of consumer interfaces in favor of a **Corporate Modern** aesthetic influenced by the precision of developer tools like Linear and the refined layering of macOS.

The interface prioritizes **high-density utility** and **calm authority**. It utilizes a "Command Center" philosophy where information is presented in a bento-grid structure to maintain organization despite high data volumes. The visual language is defined by dark, layered surfaces, razor-thin borders, and purposeful motion that signals system intelligence.

**Key Stylistic Pillars:**
- **Layered Depth:** Using varying dark tones and subtle transparency to create a sense of physical hierarchy.
- **Precision:** 1px borders and monospaced-adjacent metadata for a technical, trustworthy feel.
- **Focus:** High-contrast typography against a near-black canvas to reduce cognitive load during long sessions.

## Colors

The palette is a **Dark Mode Primary** system. It avoids pure black for surfaces, instead using a range of deep charcoals to define elevation. 

- **Primary Accent:** Spotify Green (#1DB954) is reserved strictly for interactive elements (CTAs, active toggles) and meaningful data highlights. It should never be used for large background areas.
- **Data Visualization:** A secondary Cyan/Teal is introduced for multi-series charts to provide a cool, professional contrast to the primary green.
- **Hierarchy through Luminance:** Backgrounds sit at the darkest value, while "hover" states and active cards move toward lighter grays. Text uses high-contrast white for primary content and a muted gray for secondary metadata.

## Typography

This design system utilizes **Inter** for its neutral, systematic clarity and excellent legibility at small sizes. The typographic hierarchy is designed to guide the eye from "The Big Picture" (Headlines) to "The Narrative" (Theme Sentences) to "The Evidence" (Body/Metadata).

- **Headlines:** Use tight letter-spacing and semibold weights to feel "anchored" and authoritative.
- **Theme Sentences:** Specifically designed for AI-generated summaries; larger than body text to allow for quick scanning of insights.
- **Metadata:** Smaller, often muted in color, used for timestamps, counts, and secondary labels to maintain a clean interface.
- **Numerical Data:** For tabular data or metrics, ensure the use of tabular (monospaced) figures to maintain vertical alignment in charts and tables.

## Layout & Spacing

The system follows a **Fixed-Fluid Hybrid** model. While the overall container can stretch, the internal bento-grid components respect a strict 8px/4px rhythm.

- **Bento Grid:** Home screens use a multi-column bento layout where cards span 1, 2, or 3 columns based on data priority. Gaps between cards are fixed at 16px.
- **Master-Detail:** Deep-dive screens use a split layout (30/70 or 40/60). The left panel acts as the navigation/list, while the right panel provides the expanded insights.
- **Breakpoints:**
  - **Desktop (1440px+):** Sidebar is permanent; 12-column grid.
  - **Tablet (768px - 1439px):** Sidebar collapses to icons; master-detail panels may stack.
  - **Mobile (<768px):** Single column; 16px side margins; bento cards are full-width.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layering** and **Subtle Outlines** rather than heavy drop shadows. This creates a "glass-on-glass" feel that is sophisticated and modern.

- **The Ground:** The base background is #0A0A0B.
- **Card Surfaces:** Cards use #1C1C1E with a 1px `border-subtle`.
- **Active/Hover State:** Elements lift slightly by shifting to #2C2C2E.
- **Inner Glow:** Interactive cards receive a 1px Spotify Green (#1DB954) inner border glow upon hover, signaling clickability.
- **Backdrop Blurs:** Modals and top navigation bars use a 20px blur with a semi-transparent dark tint (rgba(10, 10, 11, 0.75)) to maintain context while focusing on the foreground.

## Shapes

The shape language balances "modern approachable" with "functional precision."

- **Bento Cards & Containers:** Use a 16px to 20px radius. This softens the high-density data and gives the dashboard a premium, product-like feel.
- **Interactive Pills:** Chips, status badges, and main action buttons use a 999px (pill) radius. This clearly differentiates "actions" from "containers."
- **Data Inputs:** Use a 8px radius to feel slightly more structured than the large cards.

## Components

### Buttons & Pills
- **Primary Action:** Solid Spotify Green with black text. Pill-shaped.
- **Secondary Action:** Ghost style with `border-subtle` and white text. Pill-shaped.
- **Chips:** Used for filtering and tags. Default state is muted gray text; active state is Green text with a low-opacity green background.

### Cards (Bento-style)
- **Structure:** Cards must have a clear title (Metadata style), a main metric or visualization, and an optional footer for "View Details."
- **Hover:** Transition background from `surface-low` to `surface-high` over 150ms. Apply a subtle 2px vertical lift.

### Input Fields
- **Search:** Subtle background (#1C1C1E), 1px border, 8px radius. Use Lucide search icon.
- **Toggles:** Minimalist switch design using the primary green for the 'on' state.

### Data Visualizations
- **Charts:** No grid lines where possible. Use #1DB954 for primary data and #00F2FF for secondary comparison data.
- **Synthesis Progress:** A custom morphing component that transitions from a "Synthesize" button into a circular progress ring during data processing.

### Lists & Tables
- **Master-Detail List:** Items should be separated by a subtle 1px divider. The selected item receives a vertical 2px green indicator on its left edge.