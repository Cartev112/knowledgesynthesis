# AI Query Tab - UI Guide

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  🤖 AI Query Assistant                                          │
│  Ask questions about your knowledge graph in natural language   │
│  Powered by Neo4j Aura Agent with vector similarity search      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────┐
│  SIDEBAR         │  CHAT PANEL                                  │
│                  │                                              │
│  Example Qs      │  ┌────────────────────────────────────────┐ │
│  ┌────────────┐  │  │ 💬 Start a Conversation                │ │
│  │ What drugs │  │  │                                        │ │
│  │ target...  │  │  │ Ask me anything about your knowledge   │ │
│  └────────────┘  │  │ graph. I'll search through entities    │ │
│  ┌────────────┐  │  │ and documents to provide accurate,     │ │
│  │ Show me... │  │  │ cited answers.                         │ │
│  └────────────┘  │  └────────────────────────────────────────┘ │
│                  │                                              │
│  Settings        │  ┌────────────────────────────────────────┐ │
│  ┌────────────┐  │  │ [Type your question here...]         🚀│ │
│  │ Scope:     │  │  └────────────────────────────────────────┘ │
│  │ [Hybrid ▼] │  │                                              │
│  │            │  │                                              │
│  │ Top K: [8] │  │                                              │
│  └────────────┘  │                                              │
└──────────────────┴──────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Header Section
- **Gradient background**: Purple to violet (`#667eea` → `#764ba2`)
- **Large title**: "🤖 AI Query Assistant"
- **Description**: Explains the feature and technology
- **Styling**: Rounded corners, white text, shadow

### 2. Sidebar (Left Panel)

#### Example Questions
```
┌─────────────────────────────────────┐
│ EXAMPLE QUESTIONS                   │
├─────────────────────────────────────┤
│ What drugs target BRAF mutations?   │ ← Hover: shifts right, purple border
├─────────────────────────────────────┤
│ Show me negative relationships...   │
├─────────────────────────────────────┤
│ What are the most significant...    │
├─────────────────────────────────────┤
│ Find contradictions in the...       │
├─────────────────────────────────────┤
│ What documents discuss drug...      │
└─────────────────────────────────────┘
```

#### Settings Panel
```
┌─────────────────────────────────────┐
│ SEARCH SETTINGS                     │
├─────────────────────────────────────┤
│ Search Scope                        │
│ ┌─────────────────────────────────┐ │
│ │ Hybrid (Entities + Documents) ▼ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Top K Results                       │
│ ┌─────────────────────────────────┐ │
│ │ 8                               │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 3. Chat Panel (Right Panel)

#### Empty State
```
┌──────────────────────────────────────────┐
│                                          │
│              💬 (large icon)             │
│                                          │
│         Start a Conversation             │
│                                          │
│  Ask me anything about your knowledge    │
│  graph. I'll search through entities     │
│  and documents to provide accurate,      │
│  cited answers.                          │
│                                          │
└──────────────────────────────────────────┘
```

#### User Message
```
┌──────────────────────────────────────────┐
│                    ┌──────────────────┐  │
│                    │ What drugs target│ 👤│
│                    │ BRAF mutations?  │  │
│                    └──────────────────┘  │
│                    3:45 PM               │
└──────────────────────────────────────────┘
```
- **Right-aligned**
- **Purple gradient background**
- **White text**
- **User avatar**: 👤

#### Loading State
```
┌──────────────────────────────────────────┐
│  🤖 ┌──────────────────┐                 │
│     │ ● ● ●            │                 │
│     └──────────────────┘                 │
└──────────────────────────────────────────┘
```
- **Three animated dots**
- **Pulsing effect**
- **Gray color**

#### Assistant Message
```
┌──────────────────────────────────────────┐
│  🤖 ┌──────────────────────────────────┐ │
│     │ Based on the knowledge graph,    │ │
│     │ Vemurafenib targets BRAF V600E   │ │
│     │ mutations in melanoma.           │ │
│     │                                  │ │
│     │ ───────────────────────────────  │ │
│     │ 📚 SOURCES (2)                   │ │
│     │ ┌──────────────────────────────┐ │ │
│     │ │ 📄 Clinical Trial Results p.3│ │ │
│     │ └──────────────────────────────┘ │ │
│     │ ┌──────────────────────────────┐ │ │
│     │ │ 📄 Drug Mechanisms Study p.12│ │ │
│     │ └──────────────────────────────┘ │ │
│     │                                  │ │
│     │ ───────────────────────────────  │ │
│     │ 🔍 RETRIEVED CONTEXT             │ │
│     │ [Vemurafenib (Drug)] [BRAF...]  │ │
│     └──────────────────────────────────┘ │
│     3:45 PM                              │
└──────────────────────────────────────────┘
```
- **Left-aligned**
- **Light gray background with border**
- **Robot avatar**: 🤖
- **Sources section**: Document titles with page numbers
- **Context chips**: Yellow background, entities/documents retrieved

#### Input Area
```
┌──────────────────────────────────────────┐
│ ┌────────────────────────────────────┐   │
│ │ Ask a question about your          │ 🚀│
│ │ knowledge graph...                 │   │
│ └────────────────────────────────────┘   │
└──────────────────────────────────────────┘
```
- **Textarea**: Auto-expands with content
- **Send button**: Purple gradient, rocket icon
- **Hover effect**: Lifts up with shadow

## Color Palette

### Primary Colors
- **Purple**: `#667eea` (primary gradient start)
- **Violet**: `#764ba2` (primary gradient end)
- **Pink**: `#f093fb` → `#f5576c` (assistant avatar)

### Neutral Colors
- **White**: `#ffffff` (backgrounds)
- **Light Gray**: `#f9fafb` (message backgrounds)
- **Medium Gray**: `#9ca3af` (secondary text)
- **Dark Gray**: `#374151` (primary text)
- **Border Gray**: `#e5e7eb`

### Accent Colors
- **Yellow**: `#fef3c7` (context background)
- **Orange**: `#fbbf24` (context border)
- **Red**: `#fef2f2` (error background)

## Interaction States

### Example Button
- **Default**: Light gray background, dark text
- **Hover**: Light purple background, purple text, shifts right 4px
- **Active**: Darker purple

### Send Button
- **Default**: Purple gradient
- **Hover**: Lifts up 2px, larger shadow
- **Disabled**: 50% opacity, no hover effect

### Textarea
- **Default**: Gray border
- **Focus**: Purple border with glow effect
- **Auto-resize**: Expands from 3rem to max 10rem

## Responsive Behavior

### Desktop (>1024px)
```
┌─────────┬──────────────────┐
│ Sidebar │  Chat Panel      │
│  (33%)  │    (67%)         │
└─────────┴──────────────────┘
```

### Tablet/Mobile (<1024px)
```
┌──────────────────────────┐
│  Chat Panel              │
│  (100%, min-height 30rem)│
└──────────────────────────┘
┌──────────────────────────┐
│  Sidebar                 │
│  (100%)                  │
└──────────────────────────┘
```

## Animations

### Message Entry
- **Duration**: 0.3s
- **Effect**: Slide in from bottom + fade in
- **Easing**: ease-out

### Loading Dots
- **Duration**: 1.4s infinite
- **Effect**: Pulse (scale + opacity)
- **Stagger**: 0.16s delay between dots

### Button Hover
- **Duration**: 0.2s
- **Effect**: Transform + shadow
- **Easing**: ease

## Accessibility

- **Keyboard Navigation**: Tab through all interactive elements
- **Enter to Send**: Press Enter to send (Shift+Enter for new line)
- **Focus Indicators**: Purple glow on focused inputs
- **Color Contrast**: WCAG AA compliant
- **Screen Reader**: Semantic HTML with ARIA labels

## Browser Support

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Mobile Browsers**: Responsive layout adapts

## Performance

- **Lazy Loading**: Tab content loads only when activated
- **Auto-scroll**: Smooth scroll to bottom on new messages
- **Debouncing**: Input resize debounced for performance
- **Memory**: Messages stored in array, can be cleared
