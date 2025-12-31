# UI Improvements - Theme and Layout Settings

This document describes the new UI features added to Bemo, including light/dark mode and compact/comfortable layout options.

## Features Added

### 1. Light/Dark Mode Theme Switching
- **Light Mode**: Clean, bright interface with white backgrounds (default)
- **Dark Mode**: Dark theme with comfortable colors for reduced eye strain
- Smooth transitions between themes
- Persistent across browser sessions (stored in localStorage)
- ACE code editor automatically switches between GitHub (light) and Monokai (dark) themes

### 2. Layout Density Options
- **Comfortable Mode**: Standard spacing and padding (default)
- **Compact Mode**: Reduced spacing for more content on screen
- Affects card padding, margins, table cell padding, and navbar height
- Great for users who prefer information-dense layouts

### 3. Settings Page
- New dedicated settings page accessible from user dropdown menu
- Visual toggle switches for theme and layout
- Real-time preview of changes
- Easy-to-use interface with icons and descriptions

### 4. Quick Theme Toggle
- Theme can be toggled directly from the navbar dropdown
- Icon changes to reflect current theme (moon for light, sun for dark)
- One-click switching without navigating to settings

## How to Use

### Accessing Settings
1. Log in to your account
2. Click on your profile picture in the navbar
3. Select "Settings" from the dropdown menu

### Changing Theme
**Option 1: Via Settings Page**
1. Go to Settings page
2. Toggle the "Theme" switch
3. Theme changes instantly

**Option 2: Via Navbar**
1. Click on your profile picture
2. Click "Toggle Theme" in the dropdown
3. Theme switches immediately

### Changing Layout Density
1. Go to Settings page
2. Toggle the "Layout Density" switch
3. Choose between Comfortable and Compact

## Technical Details

### Files Added
- `bemo/static/theme.css` - CSS variables and theme definitions
- `bemo/static/theme.js` - JavaScript for theme management
- `bemo/templates/settings.html` - Settings page template

### Files Modified
- `bemo/templates/layout.html` - Added theme CSS/JS and settings menu item
- `bemo/templates/problem.html` - Updated ACE editor to respect theme
- `bemo/templates/home.html` - Cleaned up emoji usage, replaced with Bootstrap icons
- `bemo/templates/problems.html` - Cleaned up UI text
- `bemo/routes.py` - Added settings route

### CSS Variables
The theme system uses CSS custom properties (variables) for easy theming:

**Colors:**
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary` - Background colors
- `--text-primary`, `--text-secondary`, `--text-muted` - Text colors
- `--navbar-bg`, `--navbar-text` - Navbar colors
- `--card-bg`, `--card-border`, `--card-shadow` - Card styling
- `--table-bg`, `--table-hover`, `--table-border` - Table styling

**Spacing (affected by layout mode):**
- `--spacing-unit` - Base spacing unit
- `--card-padding` - Card body padding
- `--navbar-padding` - Navbar padding
- `--container-margin-top` - Main container top margin
- `--element-margin` - Standard element margins
- `--table-cell-padding` - Table cell padding

### Browser Compatibility
- Uses modern CSS features (CSS Custom Properties)
- Requires ES6 JavaScript support
- Tested on modern browsers (Chrome, Firefox, Safari, Edge)
- Uses localStorage for persistence

### Performance
- Theme changes are instant with CSS transitions
- No page reload required
- Minimal JavaScript overhead
- Settings stored locally, no server requests

## UI Improvements Summary

### Before
- Fixed light theme only
- Emoji-heavy interface
- No user customization options
- One layout density

### After
- Light and dark themes
- Cleaner icon-based interface using Bootstrap Icons
- User-customizable appearance
- Two layout density options
- Settings persist across sessions
- Smooth transitions and animations

## Screenshots

### Light Mode (Comfortable)
![Homepage Light Mode](https://github.com/user-attachments/assets/486681e0-f001-42dc-8b21-a1c41f6f3462)
![Problems Light Mode](https://github.com/user-attachments/assets/e0bdb30d-3b4c-4ae4-96a1-b97b5da4b437)

### Dark Mode (Comfortable)
![Homepage Dark Mode](https://github.com/user-attachments/assets/302580cb-b591-4827-9081-47f4d1ce6e70)
![Problems Dark Mode](https://github.com/user-attachments/assets/5abb423d-dfa6-43ba-b567-ab6fdde13ae2)

### Dark Mode (Compact)
![Homepage Dark Compact](https://github.com/user-attachments/assets/5d6b9964-e641-494f-aecb-b703aa390dd6)

## Future Enhancements

Possible additions for the future:
- Additional color themes (blue, green, etc.)
- Custom accent color picker
- Font size adjustment
- More granular spacing controls
- Theme-specific code editor color schemes
- High contrast mode for accessibility
- Auto theme based on system preferences
