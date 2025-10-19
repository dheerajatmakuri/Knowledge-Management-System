# URL Leadership Extraction Guide

## Overview
The URL Chat Interface uses intelligent pattern matching and HTML structure analysis to extract leadership information from websites.

## Extraction Strategy

### 1. **HTML Structure Analysis (Primary Method)**
The system first attempts to find leadership data by analyzing the HTML structure:

- **Sections**: Looks for `<div>` or `<section>` elements with classes like:
  - `team`, `leadership`, `executive`, `management`
  - `about`, `bio`, `profile`

- **Cards**: Within sections, finds individual member cards:
  - `card`, `member`, `person`, `profile`, `bio`

- **Name Extraction**: Finds names in:
  - `<h2>`, `<h3>`, `<h4>`, `<h5>` (headings)
  - `<strong>`, `<b>` (bold text)

- **Title Extraction**: Finds titles in:
  - `<p>`, `<span>`, `<div>` with classes like `title`, `position`, `role`, `job`

- **Image Extraction**: Finds associated `<img>` tags within the same card

### 2. **Text Pattern Matching (Fallback)**
If HTML structure analysis doesn't yield results, uses regex patterns:

- **Pattern 1**: Name on one line, title on next
  ```
  John Doe
  Chief Executive Officer
  ```

- **Pattern 2**: Name - Title or Name, Title
  ```
  John Doe - CEO
  Jane Smith, President
  ```

- **Pattern 3**: Title: Name (reverse)
  ```
  CEO: John Doe
  ```

## Leadership Title Recognition

### Priority Levels (10 = highest)

| Priority | Titles |
|----------|--------|
| 10 | CEO, Chief Executive Officer |
| 9 | President, Founder, Co-Founder |
| 8 | Chairman, Chair, CTO, CFO, COO |
| 7 | CMO, Vice President, Managing Director |
| 6 | Director, Head of, Partner |
| 5 | Executive |

## Name Validation

The system validates extracted names:
- Must be 2-4 words (e.g., "John Doe" or "Mary Jane Smith")
- Each word must start with a capital letter
- Removes extra whitespace and newlines

## Duplicate Handling

The system prevents duplicates by:
1. Tracking each unique name
2. If same name found multiple times, keeps the entry with **highest priority title**
3. Results are sorted by priority (most important titles first)

## Image Matching

Images are matched to leaders by:
1. Finding `<img>` tags within the same HTML card/container
2. Matching image `alt` text to leader names
3. Converting relative URLs to absolute URLs

## Usage Tips

### Best Results
Try these types of URLs:
- Company "About Us" pages
- "Team" or "Leadership" pages
- "Management" or "Executive Team" pages
- Individual profile pages

### Example URLs That Work Well
- `https://company.com/about-us`
- `https://company.com/team`
- `https://company.com/leadership`
- `https://company.com/company/management`

### What to Avoid
- Login-protected pages
- JavaScript-heavy SPAs (Single Page Applications)
- Pages without clear leadership information
- Generic landing pages

## Manual Review

After extraction, you can:
1. **Review Results**: Check the "Show all extracted data" option
2. **Deselect**: Uncheck leaders you don't want to save
3. **Clear**: Remove all results and try again
4. **Save**: Save selected leaders to database

## Troubleshooting

### No Leaders Found
- Try a different page (e.g., /team instead of /about)
- Check if the page requires JavaScript rendering
- Verify the page actually contains leadership information

### Wrong Data Extracted
- Use the checkbox to deselect incorrect entries
- Try a more specific page (e.g., /executive-team)
- The system prioritizes structured HTML data

### Duplicate Titles
- The system now automatically handles duplicates
- Only the highest-priority match per person is kept
- Names are deduplicated before display

### Images Not Loading
- Some images may have CORS restrictions
- Image URLs are converted to absolute paths
- Check "Show all extracted data" to see the image URL

## Database Storage

Saved leaders include:
- **Name**: Full name of the leader
- **Title**: Job title/position
- **Photo URL**: Link to profile image (if found)
- **Source URL**: Original page URL
- **Confidence Score**: 0.8 (default for pattern matching)
- **Metadata**: Extraction timestamp and method

## Future Enhancements

Planned improvements:
- Email and phone extraction from profiles
- Social media link detection (LinkedIn, Twitter)
- Bio/description extraction
- Department/team classification
- JavaScript rendering support (Selenium integration)
