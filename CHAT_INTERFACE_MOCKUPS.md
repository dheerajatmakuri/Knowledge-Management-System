# Chat Interface - UI Mockups & Screenshots Guide

## 📸 Visual Mockups

This document provides visual mockups and examples of what the chat interface looks like in action.

## 🖥️ Full Interface Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Knowledge Chat - Powered by OpenAI GPT-4                                   │
├────────────────┬────────────────────────────────────────────────────────────┤
│                │  💬 Knowledge Chat                                         │
│  SIDEBAR       │  Ask questions and get answers grounded in knowledge       │
│                │                                                             │
│  📊 Session    │  ═══════════════════════════════════════════════════════   │
│  ──────────    │                                                             │
│  Session ID:   │  ┌──────────────────────────────────────────────────────┐ │
│  streamlit_... │  │ 👤 You:                                              │ │
│  Messages: 6   │  │ What are the key differences between supervised      │ │
│                │  │ and unsupervised learning?                           │ │
│  📈 Service    │  │ ─────────────────────────────────────────────────── │ │
│  ──────────    │  │ 2024-10-16 14:30:15                                 │ │
│  Total: 150    │  └──────────────────────────────────────────────────────┘ │
│  Sessions: 8   │                                                             │
│  Avg: 2.3s     │  ┌──────────────────────────────────────────────────────┐ │
│                │  │ 🤖 Assistant:                                        │ │
│  Scope Dist:   │  │                                                      │ │
│  IN:  ████ 70% │  │ The key differences between supervised and           │ │
│  PAR: ██ 20%   │  │ unsupervised learning are:                           │ │
│  OUT: █ 10%    │  │                                                      │ │
│                │  │ 1. **Training Data**: Supervised learning uses       │ │
│  🎮 Controls   │  │    labeled data (input-output pairs), while          │ │
│  ──────────    │  │    unsupervised learning works with unlabeled data.  │ │
│  [New Chat]    │  │                                                      │ │
│  [Clear Hist]  │  │ 2. **Goal**: Supervised learning predicts outputs    │ │
│  [Download]    │  │    for new inputs, while unsupervised learning       │ │
│                │  │    discovers patterns and structure in data.         │ │
│  💾 Export     │  │                                                      │ │
│  ──────────    │  │ 3. **Examples**: Supervised includes classification  │ │
│  [Save TXT]    │  │    and regression, unsupervised includes clustering  │ │
│                │  │    and dimensionality reduction.                     │ │
│  ℹ️  Help      │  │                                                      │ │
│  ──────────    │  │ ┌────────────────┬───────────────┬───────────────┐  │ │
│  [How to use]  │  │ │ Knowledge Scope│  Confidence   │ Quality Score │  │ │
│                │  │ │  [IN SCOPE]    │  [✓ HIGH]     │     92%       │  │ │
│                │  │ └────────────────┴───────────────┴───────────────┘  │ │
│                │  │                                                      │ │
│                │  │ 📚 Sources:                                          │ │
│                │  │ ▶ Source 1: Introduction to Machine Learning        │ │
│                │  │   [Click to expand]                                  │ │
│                │  │ ▶ Source 2: ML: Supervised vs Unsupervised          │ │
│                │  │   [Click to expand]                                  │ │
│                │  │ ▶ Source 3: Understanding ML Paradigms              │ │
│                │  │   [Click to expand]                                  │ │
│                │  │                                                      │ │
│                │  │ [👍 Helpful]  [👎 Not Helpful]                       │ │
│                │  │ ─────────────────────────────────────────────────── │ │
│                │  │ 2024-10-16 14:30:18                                 │ │
│                │  └──────────────────────────────────────────────────────┘ │
│                │                                                             │
│                │  ═══════════════════════════════════════════════════════   │
│                │                                                             │
│                │  💡 Suggested Questions                                    │
│                │  ┌──────────────────────┐  ┌─────────────────────────┐   │
│                │  │ Can you provide      │  │ What are some real-world│   │
│                │  │ examples of each?    │  │ applications?           │   │
│                │  └──────────────────────┘  └─────────────────────────┘   │
│                │  ┌──────────────────────┐  ┌─────────────────────────┐   │
│                │  │ How do I choose      │  │ What are the pros and   │   │
│                │  │ between them?        │  │ cons of each?           │   │
│                │  └──────────────────────┘  └─────────────────────────┘   │
│                │                                                             │
│                │  ───────────────────────────────────────────────────────   │
│                │                                                             │
│                │  Your Question:                                            │
│                │  ┌──────────────────────────────────────────────────────┐ │
│                │  │ Type your question here...                           │ │
│                │  │                                                      │ │
│                │  │                                                      │ │
│                │  └──────────────────────────────────────────────────────┘ │
│                │  [💬 Send Message]  [🔄 Clear]                             │
│                │                                                             │
│                │  ────────────────────────────────────────────────────────  │
│                │  🤖 Powered by OpenAI GPT-4 | 🔍 Hybrid Search             │
└────────────────┴────────────────────────────────────────────────────────────┘
```

## 📋 Individual Component Mockups

### 1. User Message Card

```
┌────────────────────────────────────────────────┐
│ 👤 You:                                        │
│                                                │
│ What is the difference between AI and ML?     │
│                                                │
│ ────────────────────────────────────────────  │
│ 2024-10-16 14:25:30                           │
└────────────────────────────────────────────────┘
```

**Styling:**
- Background: Light blue (#e3f2fd)
- Left border: 4px solid blue (#2196f3)
- Padding: 12px 16px
- Border radius: 8px
- Font: Regular weight
- Timestamp: Gray, italic, small

### 2. Assistant Message Card (Collapsed)

```
┌────────────────────────────────────────────────┐
│ 🤖 Assistant:                                  │
│                                                │
│ AI (Artificial Intelligence) is a broader     │
│ concept that refers to machines performing    │
│ tasks that would normally require human       │
│ intelligence. Machine Learning (ML) is a      │
│ subset of AI that focuses on enabling         │
│ machines to learn from data without being     │
│ explicitly programmed...                      │
│                                                │
│ ┌──────────┬─────────────┬──────────────┐    │
│ │  Scope   │ Confidence  │ Quality      │    │
│ │ IN SCOPE │ ✓ HIGH      │ 88%          │    │
│ └──────────┴─────────────┴──────────────┘    │
│                                                │
│ 📚 Sources: (3)                                │
│ ▶ Source 1: AI vs ML Explained                │
│ ▶ Source 2: Understanding AI Technologies     │
│ ▶ Source 3: Machine Learning Fundamentals     │
│                                                │
│ [👍 Helpful]  [👎 Not Helpful]                 │
│ ────────────────────────────────────────────  │
│ 2024-10-16 14:25:33                           │
└────────────────────────────────────────────────┘
```

**Styling:**
- Background: Light gray (#f5f5f5)
- Left border: 4px solid green (#4caf50)
- Padding: 12px 16px
- Border radius: 8px
- Metadata: Grid layout
- Sources: Collapsible expandable

### 3. Expanded Citation

```
┌─────────────────────────────────────────────────┐
│ 📚 Source 1: AI vs ML Explained                 │
│ ─────────────────────────────────────────────   │
│                                                  │
│ "Artificial Intelligence is the simulation of   │
│  human intelligence processes by machines,       │
│  especially computer systems. These processes    │
│  include learning, reasoning, and self-          │
│  correction. Machine Learning is a subset..."    │
│                                                  │
│ 🔗 https://example.com/ai-vs-ml-explained       │
│ 👤 Author: Dr. Sarah Johnson                    │
│ 📅 Published: 2024-05-20                        │
│ 🏢 Organization: AI Research Institute          │
│                                                  │
│ ┌─────────────────┐                             │
│ │   Relevance     │                             │
│ │      91%        │                             │
│ │  ████████████▌  │                             │
│ └─────────────────┘                             │
└─────────────────────────────────────────────────┘
```

**Styling:**
- Background: Light orange (#fff3e0)
- Left border: 3px solid orange (#ff9800)
- Padding: 8px 12px
- Border radius: 4px
- Quote: Italic text
- Links: Blue, underlined
- Relevance: Progress bar

### 4. Knowledge Gap Warning

```
┌─────────────────────────────────────────────────┐
│ ⚠️  Knowledge Gaps Identified:                   │
│                                                  │
│ • No information about recent developments       │
│   after 2023                                     │
│ • Limited coverage of industry-specific          │
│   applications                                   │
│ • Missing comparisons with related technologies  │
└─────────────────────────────────────────────────┘
```

**Styling:**
- Background: Light yellow (#fff9c4)
- Icon: Warning triangle
- List: Bulleted
- Font: Regular weight
- Color: Dark gray text on yellow

### 5. Query Suggestion Chips

```
┌──────────────────────┐  ┌──────────────────────┐
│ Tell me more about   │  │ What are practical   │
│ neural networks      │  │ applications?        │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│ How do I get started │  │ Compare with deep    │
│ with machine learning│  │ learning             │
└──────────────────────┘  └──────────────────────┘
```

**Styling:**
- Background: Light purple (#e8eaf6)
- Border: 1px solid (#c5cae9)
- Padding: 6px 12px
- Border radius: 16px (pill shape)
- Font: Small, medium weight
- Hover: Darker background
- Cursor: Pointer

### 6. Scope Indicators

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  IN SCOPE   │  │   PARTIAL   │  │OUT OF SCOPE │
│   (Green)   │  │  (Orange)   │  │    (Red)    │
└─────────────┘  └─────────────┘  └─────────────┘
```

**Styling:**

**IN SCOPE:**
- Background: Green (#4caf50)
- Text: White
- Padding: 4px 12px
- Border radius: 12px
- Font: Bold, small caps

**PARTIAL SCOPE:**
- Background: Orange (#ff9800)
- Text: White
- Same dimensions as IN SCOPE

**OUT OF SCOPE:**
- Background: Red (#f44336)
- Text: White
- Same dimensions as IN SCOPE

### 7. Confidence Indicators

```
✓ HIGH CONFIDENCE     ~ MEDIUM CONFIDENCE
! LOW CONFIDENCE      ? UNCERTAIN
```

**Styling:**

| Level | Symbol | Color | Hex |
|-------|--------|-------|-----|
| HIGH | ✓ | Green | #4caf50 |
| MEDIUM | ~ | Orange | #ff9800 |
| LOW | ! | Red | #f44336 |
| UNCERTAIN | ? | Gray | #9e9e9e |

### 8. Feedback Buttons

```
┌─────────────┐  ┌──────────────┐
│ 👍 Helpful  │  │ 👎 Not Help  │
└─────────────┘  └──────────────┘

After clicking:
┌─────────────────────────────┐
│ ✓ Feedback received         │
└─────────────────────────────┘
```

**Styling:**
- Type: Secondary buttons
- Border: 1px solid gray
- Padding: 8px 16px
- Border radius: 4px
- Hover: Light gray background
- After feedback: Gray text, no buttons

### 9. Statistics Panel

```
┌──────────────────────────┐
│ 📊 Session Info          │
│ ──────────────────────   │
│                          │
│ Session ID:              │
│ streamlit_20241016_1430  │
│                          │
│ ┌──────────┐             │
│ │ Messages │             │
│ │    12    │             │
│ └──────────┘             │
│                          │
│ 📈 Service Stats         │
│ ──────────────────────   │
│                          │
│ ┌───────┬──────┐         │
│ │ Total │ 150  │         │
│ │Queries│      │         │
│ └───────┴──────┘         │
│                          │
│ ┌───────┬──────┐         │
│ │Active │  8   │         │
│ │Session│      │         │
│ └───────┴──────┘         │
│                          │
│ ┌───────┬──────┐         │
│ │ Avg   │ 2.3s │         │
│ │ Time  │      │         │
│ └───────┴──────┘         │
│                          │
│ Scope Distribution:      │
│ ──────────────────────   │
│ IN:      ████████ 70%    │
│ PARTIAL: ███ 20%         │
│ OUT:     █ 10%           │
└──────────────────────────┘
```

**Styling:**
- Background: Light gray sidebar
- Sections: Separated by dividers
- Metrics: Card-style boxes
- Progress bars: Colored by scope
- Font: Smaller than main content

### 10. Help Section

```
┌──────────────────────────┐
│ ℹ️  Help                  │
│ ──────────────────────   │
│                          │
│ ▶ How to use             │
│ ────────────────────     │
│                          │
│ Getting Started:         │
│ 1. Type your question    │
│ 2. Click suggested       │
│    questions for quick   │
│    queries               │
│ 3. View sources and      │
│    citations             │
│                          │
│ Understanding Indicators:│
│ • 🟢 IN SCOPE: Complete  │
│ • 🟠 PARTIAL: Some info  │
│ • 🔴 OUT: No information │
│                          │
│ Confidence Levels:       │
│ • ✓ HIGH: Strong         │
│ • ~ MEDIUM: Moderate     │
│ • ! LOW: Limited         │
│ • ? UNCERTAIN: Cannot    │
│                          │
│ Features:                │
│ • Source citations       │
│ • Knowledge gaps         │
│ • Context-aware          │
│ • Quality feedback       │
└──────────────────────────┘
```

**Styling:**
- Expandable section
- Markdown formatting
- Lists: Bulleted
- Icons: Emoji-based
- Font: Smaller, regular weight

## 🎬 User Flow Visualizations

### Flow 1: First-Time User

```
User Opens Interface
         │
         ▼
    Welcome Screen
    (Empty chat)
         │
         ├─▶ Sees "Start a conversation" message
         ├─▶ Sees 4 default suggestions
         └─▶ Sees empty input box
         │
         ▼
   Clicks Suggestion
   "What topics are covered?"
         │
         ▼
    Shows Spinner
    "🤔 Thinking..."
         │
         ▼
   Response Appears
         ├─▶ Answer text
         ├─▶ IN SCOPE indicator
         ├─▶ HIGH confidence
         ├─▶ 3 citations
         └─▶ Quality score: 89%
         │
         ▼
   New Suggestions Appear
   (Context-aware)
         │
         ▼
   User Continues Chatting
```

### Flow 2: Multi-Turn Conversation

```
Turn 1: "What is AI?"
    Response with citations
         │
         ▼
Turn 2: "How does it work?"
    Response references Turn 1
         │
         ▼
Turn 3: "Give me an example"
    Response builds on previous context
         │
         ▼
Turn 4: "What are the limitations?"
    Response considers full conversation
```

**Context Preserved:**
- Previous questions remembered
- Pronouns ("it") understood
- Topic continuity maintained
- Citations accumulate

### Flow 3: Exploring Citations

```
User Receives Response
         │
         ▼
    Sees Citation List
    ▶ Source 1: [Title]
    ▶ Source 2: [Title]
    ▶ Source 3: [Title]
         │
         ▼
   Clicks Source 1
         │
         ▼
   Expands to Show:
    ├─▶ Full snippet
    ├─▶ Author name
    ├─▶ Published date
    ├─▶ URL (clickable)
    └─▶ Relevance: 91%
         │
         ▼
    Clicks URL
         │
         ▼
   Opens Original Source
   (in new tab)
```

### Flow 4: Providing Feedback

```
User Reads Response
         │
         ▼
    Evaluates Quality
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Helpful   Not Helpful
    │         │
    ▼         ▼
  Click     Click
  👍        👎
    │         │
    └────┬────┘
         │
         ▼
    Success Message
    "Thanks for feedback!"
         │
         ▼
    Buttons Disappear
    Replaced with:
    "✓ Feedback received"
```

### Flow 5: Starting New Conversation

```
Current Conversation
(6 messages)
         │
         ▼
   User Clicks
   "New Conversation"
         │
         ▼
    Confirmation?
    (Optional future feature)
         │
         ▼
    New Session Created
         ├─▶ New session ID
         ├─▶ Messages cleared
         ├─▶ Responses cleared
         ├─▶ Feedback reset
         └─▶ Default suggestions
         │
         ▼
    Empty Chat Interface
    Ready for new topic
```

## 📊 State Diagrams

### Message State Machine

```
    [EMPTY]
       │
       │ User types & sends
       ▼
 [USER MESSAGE]
       │
       │ Service processes
       ▼
  [PROCESSING]
    (spinner)
       │
       │ Response ready
       ▼
[ASSISTANT MESSAGE]
       │
       ├─▶ Display metadata
       ├─▶ Show citations
       ├─▶ Enable feedback
       └─▶ Update suggestions
       │
       │ User continues
       ▼
 [USER MESSAGE]
  (new message)
```

### Feedback State Machine

```
  [NO FEEDBACK]
       │
       │ User clicks 👍 or 👎
       ▼
[FEEDBACK PENDING]
       │
       │ Record feedback
       ▼
[FEEDBACK RECEIVED]
       │
       │ Show confirmation
       ▼
[FEEDBACK COMPLETE]
    (buttons hidden)
```

### Session State Machine

```
  [INITIAL]
       │
       │ First query
       ▼
   [ACTIVE]
       │
       ├─▶ Continue chatting
       │   (stays ACTIVE)
       │
       ├─▶ Clear history
       │   (stays ACTIVE,
       │    clears messages)
       │
       └─▶ New conversation
           │
           ▼
        [RESET]
           │
           └─▶ Back to INITIAL
```

## 🎨 Color Reference

### Primary Colors

```
User Interface:
┌────────────────┬──────────┬───────────┐
│ Element        │ Color    │ Hex       │
├────────────────┼──────────┼───────────┤
│ User Message   │ Blue     │ #2196f3   │
│ Assistant Msg  │ Green    │ #4caf50   │
│ IN SCOPE       │ Green    │ #4caf50   │
│ PARTIAL SCOPE  │ Orange   │ #ff9800   │
│ OUT OF SCOPE   │ Red      │ #f44336   │
│ HIGH Confidence│ Green    │ #4caf50   │
│ MEDIUM Conf    │ Orange   │ #ff9800   │
│ LOW Confidence │ Red      │ #f44336   │
│ UNCERTAIN      │ Gray     │ #9e9e9e   │
│ Citation Box   │ Orange   │ #ff9800   │
│ Suggestion     │ Purple   │ #3f51b5   │
│ Metadata       │ Gray     │ #757575   │
└────────────────┴──────────┴───────────┘
```

### Background Colors

```
Backgrounds:
┌────────────────┬──────────────┬───────────┐
│ Element        │ Color        │ Hex       │
├────────────────┼──────────────┼───────────┤
│ User Msg BG    │ Light Blue   │ #e3f2fd   │
│ Assistant BG   │ Light Gray   │ #f5f5f5   │
│ Citation BG    │ Light Orange │ #fff3e0   │
│ Suggestion BG  │ Light Purple │ #e8eaf6   │
│ Warning BG     │ Light Yellow │ #fff9c4   │
│ Sidebar BG     │ Light Gray   │ #fafafa   │
└────────────────┴──────────────┴───────────┘
```

## 📱 Responsive Behavior

### Desktop (1920x1080)
- Sidebar: 250px fixed width
- Main content: Remaining space
- Layout: Side-by-side
- Font: 16px base

### Tablet (768x1024)
- Sidebar: Collapsible
- Main content: Full width when sidebar closed
- Layout: Flexible
- Font: 16px base

### Mobile (375x667)
- Sidebar: Hidden by default
- Main content: Full width
- Layout: Stacked
- Font: 14px base

## 🎯 Interactive Elements

### Hover States

**Suggestion Chips:**
```
Normal:  [Background: #e8eaf6, Border: #c5cae9]
Hover:   [Background: #c5cae9, Border: #9fa8da]
Active:  [Background: #9fa8da, Border: #7986cb]
```

**Citation Headers:**
```
Normal:  [▶ Source 1: Title...]
Hover:   [▶ Source 1: Title...]  (pointer cursor)
Clicked: [▼ Source 1: Title...]  (expanded)
```

**Feedback Buttons:**
```
Normal:  [Border: gray, Background: white]
Hover:   [Border: blue, Background: #f0f0f0]
Clicked: [Border: green, Background: #e0ffe0]
After:   [Text only: "✓ Feedback received"]
```

---

**This visual guide helps developers and designers understand the complete look and feel of the chat interface!**