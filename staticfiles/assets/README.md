# Asset Tracker - Static Files

This directory contains the CSS and JavaScript files for the Asset Tracker application.

## Structure

```
assets/static/assets/
├── css/
│   ├── styles.css      # Main stylesheet with all core styles
│   └── mobile.css      # Mobile-specific responsive enhancements
└── js/
    └── main.js         # Main JavaScript for interactions and enhancements
```

## CSS Files

### styles.css
Main stylesheet containing:
- **Base Styles**: Reset, typography, layout
- **Navigation**: Navbar styling with active states
- **Buttons**: Primary, secondary, warning, danger, success variants
- **Tables**: Responsive table layouts with hover effects
- **Forms**: Form controls, validation states, error messages
- **Alerts**: Info, success, warning, danger alert styles
- **Warranty Highlighting**: Special styles for expiring/expired warranties
- **Status Badges**: Color-coded status indicators
- **Attachments**: File attachment display styles
- **IP Ranges**: Grid layout for IP address display
- **Responsive Design**: Breakpoints at 992px, 768px, and 480px
- **Print Styles**: Optimized for printing

### mobile.css
Mobile-specific enhancements:
- **Mobile Tables**: Stacked table layout for small screens
- **Touch-Friendly**: Minimum 44px touch targets (iOS guidelines)
- **Mobile Navigation**: Full-width navigation items
- **Form Improvements**: Prevents iOS zoom, custom select styling
- **Sticky Header**: Fixed navigation on scroll
- **Landscape Support**: Optimized for landscape orientation
- **Tablet Adjustments**: Specific styles for 769px-992px
- **Small Phone**: Extra adjustments for screens < 360px
- **Accessibility**: Enhanced focus indicators for touch devices
- **Dark Mode**: Optional dark mode support (commented out)

## JavaScript Features

### main.js
Interactive features:
- **Confirmation Dialogs**: Prompts for delete/scrap actions
- **Form Validation**: Real-time validation with error highlighting
- **File Upload**: Shows selected file name
- **Table Sorting**: Click column headers to sort (with ▲▼ indicators)
- **Table Search**: Quick search functionality (optional, commented out)
- **Loading States**: Disables submit buttons during processing
- **Auto-dismiss Alerts**: Success messages fade after 5 seconds
- **Warranty Highlighting**: Fade-in animation for highlighted rows
- **Keyboard Shortcuts**:
  - `Alt+N`: Create new asset (if admin)
  - `Escape`: Cancel/go back
- **Responsive Tables**: Adds data labels for mobile view

## Usage

The static files are automatically loaded in the base template:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'assets/css/styles.css' %}">
<link rel="stylesheet" href="{% static 'assets/css/mobile.css' %}">
<script src="{% static 'assets/js/main.js' %}"></script>
```

## Customization

### Adding Custom Styles
Use the `extra_css` block in templates:

```html
{% block extra_css %}
.custom-class {
    color: red;
}
{% endblock %}
```

### Adding Custom JavaScript
Use the `extra_js` block in templates:

```html
{% block extra_js %}
<script>
    // Custom JavaScript
</script>
{% endblock %}
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- iOS Safari: iOS 12+
- Chrome Android: Latest version

## Responsive Breakpoints

- **Desktop**: > 992px
- **Tablet**: 769px - 992px
- **Mobile**: ≤ 768px
- **Small Phone**: ≤ 480px
- **Extra Small**: ≤ 360px

## Features by Requirement

### Table Layouts
- Responsive tables with horizontal scroll on mobile
- Hover effects for better UX
- Sortable columns with visual indicators
- Mobile-stacked layout for small screens

### Buttons
- Multiple variants (primary, secondary, warning, danger, success)
- Hover effects with subtle animations
- Touch-friendly sizing on mobile (44px minimum)
- Loading states during form submission

### Forms
- Consistent styling across all form elements
- Real-time validation feedback
- Error highlighting with red borders
- Help text and required field indicators
- File upload with filename display

### Confirmation Dialogs
- JavaScript-based confirmation for destructive actions
- Password confirmation for freeing assets
- Visual warnings with color-coded alerts

### Warranty Row Highlighting
- Yellow background for warranties expiring within 7 days
- Red background for expired warranties
- Status badges with color coding
- Fade-in animation on page load

### Responsive Design
- Mobile-first approach
- Breakpoints for tablet and desktop
- Touch-friendly interface elements
- Sticky navigation on mobile
- Optimized for both portrait and landscape

## Performance

- Minimal CSS (~15KB uncompressed)
- Minimal JavaScript (~8KB uncompressed)
- No external dependencies
- Efficient selectors and animations
- Print-optimized styles

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators for all interactive elements
- Color contrast meets WCAG AA standards
- Touch targets meet iOS guidelines (44px)

## Maintenance

To update styles:
1. Edit the CSS files in `assets/static/assets/css/`
2. Run `python manage.py collectstatic` to copy to staticfiles
3. Clear browser cache or use hard refresh (Ctrl+F5)

To update JavaScript:
1. Edit `assets/static/assets/js/main.js`
2. Run `python manage.py collectstatic`
3. Clear browser cache or use hard refresh (Ctrl+F5)
