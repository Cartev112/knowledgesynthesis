# Knowledge Graph Visual Alphabet

This document defines the visual language used in the Knowledge Synthesis Platform's graph visualization. Consistent visual cues help users quickly understand the graph's structure and data quality.

## Node Styling

### Node Size
**Property**: `significance` (1-5 scale)
- **Size Range**: 40px (significance=1) to 80px (significance=5)
- **Formula**: `30 + significance × 10`
- **Purpose**: Larger nodes represent more important/central concepts in the knowledge base
- **Example**: A core concept like "BRAF V600E mutation" might have significance=5 (80px), while a peripheral mention has significance=1 (40px)

### Node Color
**Property**: Search/selection state
- **Default Blue** (`#667eea`): Standard entity node
- **Red** (`#dc2626`): Highlighted/searched node - the primary focus of current query
- **Orange** (`#f59e0b`): Neighbor node - directly connected to highlighted nodes
- **Purple** (`#8b5cf6`): Multi-selected node - chosen for batch review
- **Dark Blue** (`#1d4ed8`): Currently selected node (clicked)

### Node Border
**Property**: Verification status (future enhancement)
- **Solid border**: Verified entities (confirmed by domain experts)
- **Dashed border**: Unverified entities (needs expert review)
- **Border Width**: 2-4px depending on state

## Edge (Relationship) Styling

### Edge Width
**Property**: `significance` (1-5 scale) AND source count
- **Significance-based**: 1.8px (sig=1) to 5px (sig=5)
  - Formula: `1 + significance × 0.8`
- **Source-based** (future): Thickness increases with number of supporting documents
  - 1 source: 2px
  - 2-3 sources: 3px
  - 4+ sources: 4px
- **Purpose**: Thicker edges indicate more important or well-supported relationships

### Edge Color
**Property**: Verification status
- **Gray** (`#94a3b8`): Unverified relationship (default)
- **Green** (`#059669`): Verified relationship (confirmed by expert)
- **Red** (`#dc2626`): Incorrect relationship (flagged by expert)

### Edge Style
**Property**: Relationship polarity
- **Solid line**: Positive relationship (e.g., "activates", "causes")
- **Dotted line**: Negative relationship (e.g., "does_not_activate", "inhibits")
- **Dashed line**: Incorrect/flagged relationship

### Edge Label
**Property**: Relationship type
- **Text**: Predicate name (e.g., "targets", "inhibits")
- **Background**: White with 80% opacity for readability
- **Rotation**: Auto-rotates to follow edge direction

## Status Indicators

### Verification Status Badges
Used in detail panels and review queue:
- **Unverified**: Yellow background (`#fef3c7`), brown text (`#92400e`)
- **Verified**: Green background (`#d1fae5`), dark green text (`#065f46`)
- **Incorrect**: Red background (`#fee2e2`), dark red text (`#991b1b`)

### Significance Stars
Used in detail panels:
- **Display**: ⭐⭐⭐⭐⭐ (filled) + ☆☆ (empty)
- **Color**: Gold (`#f59e0b`)
- **Scale**: 1-5 stars
- **Purpose**: Quick visual assessment of importance

## Interactive States

### Hover Effects
- **Nodes**: Slight brightness increase
- **Edges**: Width increases by 1px, color darkens slightly

### Selection States
- **Single Select**: Dark blue background, thicker border
- **Multi-Select**: Purple background, thicker border
- **Highlighted**: Red background with highest z-index (appears on top)

## Layout & Spacing

### Graph Layout
- **Algorithm**: Force-directed (COSE) for natural clustering
- **Node Overlap**: Minimum 10-20px spacing
- **Edge Length**: Ideal 100-120px
- **Padding**: 30-50px around viewport

### Detail Panel
- **Position**: Right side, slides in when node/edge clicked
- **Width**: 25% of viewport (minimum 300px)
- **Sections**: Separated by light gray borders

## Color Palette

### Primary Colors
- **Primary Blue**: `#667eea` - Default nodes, primary buttons
- **Purple**: `#764ba2` - Gradients, accents
- **Green**: `#059669` - Success, verified status
- **Red**: `#dc2626` - Errors, incorrect status, highlighted nodes
- **Orange**: `#f59e0b` - Warnings, neighbor nodes, significance stars

### Neutral Colors
- **Gray 50**: `#f9fafb` - Backgrounds
- **Gray 200**: `#e5e7eb` - Borders
- **Gray 400**: `#9ca3af` - Disabled states
- **Gray 600**: `#6b7280` - Secondary text
- **Gray 900**: `#111827` - Primary text

## Accessibility Considerations

### Color Blindness
- Don't rely solely on color - use shape, size, and patterns
- Red/green states also have different border styles
- Text labels always present on edges

### Contrast
- All text meets WCAG AA standards (4.5:1 minimum)
- White text on colored backgrounds uses sufficient opacity

### Keyboard Navigation
- Tab through interactive elements
- Enter/Space to select
- Arrow keys to navigate (future enhancement)

## Future Enhancements

### Planned Visual Features
1. **Node clustering by type**: Different shapes for Drug, Gene, Disease, etc.
2. **Temporal indicators**: Gradient or glow for recently added nodes
3. **Confidence visualization**: Opacity based on confidence score
4. **Community detection**: Color groups for densely connected subgraphs
5. **Path highlighting**: Animated paths between selected nodes
6. **Heatmap mode**: Color intensity based on connection density

### Animation Guidelines
- **Duration**: 200-300ms for state changes
- **Easing**: Ease-out for natural feel
- **Performance**: Limit animations to <100 elements simultaneously

---

**Last Updated**: 2025-10-06  
**Version**: 1.0  
**Maintained By**: Knowledge Synthesis Platform Team
