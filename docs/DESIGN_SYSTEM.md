# Design System - Table Automation Application

> **Complete design reference for consistent UI/UX across applications**
> Version: 1.0 | Last Updated: January 2025

---

## Table of Contents
1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing & Layout](#spacing--layout)
4. [Components](#components)
5. [Shadows & Effects](#shadows--effects)
6. [Animations](#animations)
7. [Responsive Design](#responsive-design)

---

## Color Palette

### Primary Colors
```css
--primary: #0066FF;           /* Main brand color - bright blue */
--primary-dark: #0052CC;      /* Darker variant for hover states */
--primary-light: #3384FF;     /* Lighter variant for backgrounds */
--accent: #00D9FF;            /* Accent color - cyan */
```

**Usage:**
- Primary: Main action buttons, active states, links
- Primary Dark: Hover states on primary buttons
- Primary Light: Highlights, selected items
- Accent: Secondary highlights, gradients, special elements

### Status Colors
```css
--success: #00C853;           /* Green - success states */
--warning: #FF9500;           /* Orange - warning states */
--error: #FF3B30;             /* Red - error states */
```

**Usage:**
- Success: Success messages, completed states
- Warning: Warning messages, caution states
- Error: Error messages, validation failures

### Background Colors
```css
--bg-main: #0A0E14;           /* Main application background */
--bg-secondary: #12161E;      /* Secondary background (cards, sections) */
--bg-tertiary: #1A1F2B;       /* Tertiary background (nested elements) */
--bg-card: #1E2430;           /* Card backgrounds */
```

**Usage:**
- Main: Body background
- Secondary: Panel backgrounds, sections
- Tertiary: Nested components, dropdowns
- Card: Individual card components

### Text Colors
```css
--text-primary: #FFFFFF;      /* Primary text - white */
--text-secondary: #A0A8B8;    /* Secondary text - light gray */
--text-tertiary: #6C7486;     /* Tertiary text - medium gray */
```

**Usage:**
- Primary: Main headings, important text
- Secondary: Body text, descriptions
- Tertiary: Hints, placeholders, disabled text

### Border & Divider
```css
--border: #2A3142;            /* Border color */
```

**Usage:**
- Borders, dividers, outlines

### Gradients
```css
/* Background gradient */
background: linear-gradient(135deg, #0A0E14 0%, #12161E 100%);

/* Header gradient */
background: linear-gradient(90deg, var(--primary), var(--accent));

/* Text gradient */
background: linear-gradient(135deg, var(--text-primary), var(--accent));
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;

/* Card highlight gradient */
background: linear-gradient(135deg, rgba(0, 102, 255, 0.1), rgba(0, 217, 255, 0.1));
```

---

## Typography

### Font Families
```css
/* Primary font - for UI elements */
font-family: 'Urbanist', -apple-system, BlinkMacSystemFont, sans-serif;

/* Monospace font - for code, technical data */
font-family: 'JetBrains Mono', monospace;
```

### Font Sizes
```css
/* Headings */
--font-size-h1: 28px;         /* Main page title */
--font-size-h2: 24px;         /* Section headings */
--font-size-h3: 18px;         /* Subsection headings */
--font-size-h4: 16px;         /* Card titles */
--font-size-h5: 15px;         /* Small headings */

/* Body text */
--font-size-body: 14px;       /* Default body text */
--font-size-small: 13px;      /* Small text */
--font-size-tiny: 12px;       /* Very small text, labels */
--font-size-micro: 11px;      /* Micro text */
```

### Font Weights
```css
--font-weight-light: 300;     /* Light text */
--font-weight-regular: 400;   /* Regular text */
--font-weight-medium: 500;    /* Medium emphasis */
--font-weight-semibold: 600;  /* Semi-bold headings */
--font-weight-bold: 700;      /* Bold headings */
--font-weight-extrabold: 800; /* Extra bold titles */
```

### Line Heights
```css
--line-height-tight: 1.4;     /* Tight spacing (headings) */
--line-height-normal: 1.6;    /* Normal spacing (body) */
--line-height-relaxed: 1.8;   /* Relaxed spacing (reading) */
```

### Letter Spacing
```css
--letter-spacing-tight: -0.5px;   /* Headings */
--letter-spacing-normal: 0;       /* Body text */
--letter-spacing-wide: 0.5px;     /* Uppercase labels */
```

---

## Spacing & Layout

### Border Radius
```css
--radius: 12px;               /* Default border radius */
--radius-sm: 8px;             /* Small border radius */
--radius-lg: 16px;            /* Large border radius */
--radius-full: 9999px;        /* Fully rounded (pills, circles) */
```

### Shadows
```css
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
```

### Spacing Scale
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 12px;
--space-lg: 16px;
--space-xl: 20px;
--space-2xl: 24px;
--space-3xl: 32px;
--space-4xl: 48px;
```

### Container Widths
```css
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
--container-max: 1900px;       /* Application max width */
```

---

## Components

### Buttons

#### Primary Button
```css
.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    border: none;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 102, 255, 0.4);
}

.btn-primary:active {
    transform: translateY(0);
}
```

#### Secondary Button
```css
.btn-secondary {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border);
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    font-weight: 500;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: var(--bg-card);
    border-color: var(--primary);
}
```

#### Success Button
```css
.btn-success {
    background: linear-gradient(135deg, var(--success), #00A844);
    color: white;
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    border: none;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 200, 83, 0.3);
}
```

#### Small Button
```css
.btn-small {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 6px;
}
```

### Cards

#### Basic Card
```css
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    box-shadow: var(--shadow-md);
}
```

#### Panel Card
```css
.panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    box-shadow: var(--shadow-md);
    display: flex;
    flex-direction: column;
}
```

### Form Elements

#### Input Field
```css
.form-input {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    color: var(--text-primary);
    font-size: 14px;
    width: 100%;
    transition: all 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
}

.form-input::placeholder {
    color: var(--text-tertiary);
}
```

#### Select Dropdown
```css
.form-select {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    color: var(--text-primary);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.form-select:hover {
    border-color: var(--primary);
}
```

#### Label
```css
.form-label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
}
```

### Alerts

#### Alert Base
```css
.alert {
    padding: 14px 18px;
    border-radius: var(--radius-sm);
    margin-bottom: 16px;
    font-size: 14px;
    animation: slideDown 0.3s ease-out;
}
```

#### Alert Success
```css
.alert-success {
    background: rgba(0, 200, 83, 0.15);
    border: 1px solid var(--success);
    color: var(--success);
}
```

#### Alert Error
```css
.alert-error {
    background: rgba(255, 59, 48, 0.15);
    border: 1px solid var(--error);
    color: var(--error);
}
```

#### Alert Warning
```css
.alert-warning {
    background: rgba(255, 149, 0, 0.15);
    border: 1px solid var(--warning);
    color: var(--warning);
}
```

### Modal

#### Modal Overlay
```css
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
}
```

#### Modal Container
```css
.modal {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow: hidden;
    animation: slideUp 0.3s ease-out;
}
```

#### Modal Header
```css
.modal-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
}
```

#### Modal Content
```css
.modal-content {
    padding: 24px;
    overflow-y: auto;
    max-height: calc(90vh - 140px);
}
```

#### Modal Footer
```css
.modal-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    display: flex;
    gap: 12px;
    justify-content: flex-end;
}
```

### Table

#### Table Container
```css
.table-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
}
```

#### Table
```css
.table {
    width: 100%;
    border-collapse: collapse;
}

.table thead {
    background: var(--bg-tertiary);
}

.table th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border);
}

.table td {
    padding: 12px 16px;
    font-size: 14px;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
}

.table tr:hover {
    background: var(--bg-tertiary);
}
```

### Badge
```css
.badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    background: var(--primary);
    color: white;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
```

### Divider
```css
.divider {
    height: 1px;
    background: var(--border);
    margin: 20px 0;
}
```

---

## Shadows & Effects

### Box Shadows
```css
/* Small elevation */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);

/* Medium elevation */
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);

/* Large elevation */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);

/* Button hover glow */
box-shadow: 0 6px 20px rgba(0, 102, 255, 0.4);

/* Success button glow */
box-shadow: 0 4px 12px rgba(0, 200, 83, 0.3);
```

### Backdrop Blur
```css
backdrop-filter: blur(4px);   /* Modal overlay */
backdrop-filter: blur(8px);   /* Strong blur effect */
```

---

## Animations

### Keyframe Animations
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideRight {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
```

### Transition Timing
```css
/* Quick transitions */
transition: all 0.2s ease;

/* Standard transitions */
transition: all 0.3s ease;

/* Transform animations */
transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);

/* Color transitions */
transition: color 0.2s ease, background 0.2s ease;
```

---

## Responsive Design

### Breakpoints
```css
/* Mobile */
@media (max-width: 640px) { }

/* Tablet */
@media (max-width: 768px) { }

/* Desktop */
@media (max-width: 1024px) { }

/* Large Desktop */
@media (max-width: 1280px) { }
```

### Grid System
```css
/* Two column layout */
.grid-2 {
    display: grid;
    grid-template-columns: 1fr 480px;
    gap: 24px;
}

/* Three column layout */
.grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
}

/* Responsive grid */
.grid-responsive {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
}
```

---

## Usage Examples

### Complete Button Set
```html
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
<button class="btn btn-success">Success Action</button>
<button class="btn btn-small btn-primary">Small Button</button>
```

### Complete Form
```html
<div class="form-group">
    <label class="form-label">Input Label</label>
    <input type="text" class="form-input" placeholder="Enter text...">
</div>

<div class="form-group">
    <label class="form-label">Select Label</label>
    <select class="form-select">
        <option>Option 1</option>
        <option>Option 2</option>
    </select>
</div>
```

### Complete Card
```html
<div class="card">
    <h3>Card Title</h3>
    <p>Card content goes here...</p>
</div>
```

### Complete Modal
```html
<div class="modal-overlay">
    <div class="modal">
        <div class="modal-header">Modal Title</div>
        <div class="modal-content">
            Modal content...
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary">Cancel</button>
            <button class="btn btn-primary">Confirm</button>
        </div>
    </div>
</div>
```

---

## Best Practices

### Color Usage
1. **Primary color** for main actions and brand elements
2. **Accent color** sparingly for highlights and special elements
3. **Status colors** only for their specific purposes
4. Maintain **contrast ratio of at least 4.5:1** for text

### Typography
1. Use **Urbanist** for all UI elements
2. Use **JetBrains Mono** only for code and technical data
3. Maintain **consistent hierarchy** with font sizes
4. Keep **line-height at 1.6** for body text

### Spacing
1. Use **multiples of 4px** for spacing
2. Maintain **consistent padding** in similar components
3. Use **24px** as standard component padding
4. Keep **gaps at 12px or 24px** in grids

### Animations
1. Keep animations **under 300ms**
2. Use **ease or ease-out** timing functions
3. Animate **only transform and opacity** for performance
4. Provide **reduced motion** alternatives

### Accessibility
1. Maintain **proper color contrast**
2. Include **focus states** for all interactive elements
3. Use **semantic HTML** elements
4. Provide **keyboard navigation** support

---

## Color Accessibility Matrix

| Foreground | Background | Contrast Ratio | WCAG AA | WCAG AAA |
|------------|------------|----------------|---------|----------|
| #FFFFFF    | #0066FF    | 4.57:1        | ✓       | ✗        |
| #FFFFFF    | #0A0E14    | 15.84:1       | ✓       | ✓        |
| #A0A8B8    | #0A0E14    | 7.23:1        | ✓       | ✓        |
| #6C7486    | #0A0E14    | 4.52:1        | ✓       | ✗        |

---

## Notes for Implementation

1. **CSS Variables**: Use CSS custom properties (variables) for easy theme switching
2. **Component Consistency**: Maintain consistent styling across all components
3. **Dark Theme Optimized**: This design system is optimized for dark themes
4. **Scalability**: All measurements use relative units where appropriate
5. **Performance**: Animations use GPU-accelerated properties (transform, opacity)

---

**Design System Version**: 1.0
**Last Updated**: January 2025
**Maintained by**: Viriya Thawaro
**Application**: Table-Based Script Automation
