"""
Enhanced Streamlit Chat Interface with URL Scraping Capabilities

This interface allows users to:
1. Input a URL to scrape content
2. Ask follow-up questions about the scraped content
3. Extract specific information (leadership, images, etc.)
4. Store extracted data in SQLite database

Author: Knowledge Management System
Date: 2025-10-16
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from urllib.parse import urljoin

import streamlit as st
import requests
from bs4 import BeautifulSoup
from loguru import logger
import validators

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.chat_service import ChatService, ChatResponse, ResponseConfidence, KnowledgeScope
from src.database.repository import DatabaseSession, ProfileRepository
from src.database.models import Profile, Content


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="URL Knowledge Chat",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .url-input-container {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 20px 0;
    }
    
    .scraped-content {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 8px;
        max-height: 400px;
        overflow-y: auto;
        margin: 10px 0;
    }
    
    .leadership-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .extraction-result {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if 'chat_service' not in st.session_state:
        st.session_state.chat_service = None
    
    if 'db_session' not in st.session_state:
        st.session_state.db_session = DatabaseSession()
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"url_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_url' not in st.session_state:
        st.session_state.current_url = None
    
    if 'scraped_content' not in st.session_state:
        st.session_state.scraped_content = None
    
    if 'extracted_leaders' not in st.session_state:
        st.session_state.extracted_leaders = []


# ============================================================================
# URL SCRAPING FUNCTIONS
# ============================================================================

def find_leadership_page(base_url: str, soup: BeautifulSoup) -> Optional[str]:
    """
    Automatically find the leadership page URL from the current page.
    
    Args:
        base_url: The base URL of the website
        soup: BeautifulSoup object of the current page
        
    Returns:
        Leadership page URL if found, None otherwise
    """
    logger.info(f"🔍 Searching for leadership page on {base_url}")
    
    # Keywords to look for in links
    leadership_keywords = [
        'leadership', 'leaders', 'team', 'executive', 'management',
        'our-team', 'our-leadership', 'about-us/team', 'about/leadership',
        'company/leadership', 'who-we-are', 'management-team', 'executive-team',
        'board', 'directors', 'executives', 'c-suite', 'officer'
    ]
    
    testimonial_keywords = ['testimonial', 'review', 'customer', 'client', 'case-stud']
    
    found_links = []
    
    # Search all links on the page
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        link_text = link.get_text().strip().lower()
        
        # Skip testimonial/customer pages
        if any(kw in href or kw in link_text for kw in testimonial_keywords):
            continue
        
        # Check if link matches leadership keywords
        for keyword in leadership_keywords:
            if keyword in href or keyword in link_text:
                full_url = urljoin(base_url, link['href'])
                priority = 0
                
                # Priority scoring
                if 'leadership' in href or 'leadership' in link_text:
                    priority = 10
                elif 'team' in href or 'team' in link_text:
                    priority = 9
                elif 'executive' in href or 'executive' in link_text:
                    priority = 8
                elif 'management' in href or 'management' in link_text:
                    priority = 7
                elif 'about' in href:
                    priority = 5
                else:
                    priority = 6
                
                found_links.append({
                    'url': full_url,
                    'text': link.get_text().strip(),
                    'priority': priority,
                    'href': href
                })
                break
    
    # Remove duplicates and sort by priority
    unique_links = {}
    for link in found_links:
        if link['url'] not in unique_links:
            unique_links[link['url']] = link
    
    sorted_links = sorted(unique_links.values(), key=lambda x: x['priority'], reverse=True)
    
    if sorted_links:
        best_match = sorted_links[0]
        logger.success(f"✅ Found leadership page: {best_match['url']} (text: '{best_match['text']}')")
        return best_match['url']
    
    logger.warning(f"⚠️ No leadership page found on {base_url}")
    return None


def scrape_url(url: str, auto_navigate: bool = True) -> Dict[str, Any]:
    """
    Scrape content from a URL with automatic navigation to leadership page.
    
    Args:
        url: URL to scrape
        auto_navigate: If True, automatically navigate to leadership page if found
        
    Returns:
        Dictionary with scraped content
    """
    try:
        logger.info(f"Scraping URL: {url}")
        
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find leadership page automatically
        leadership_url = None
        if auto_navigate:
            leadership_url = find_leadership_page(url, soup)
            if leadership_url and leadership_url != url:
                logger.info(f"🔄 Auto-navigating to leadership page: {leadership_url}")
                # Recursively scrape the leadership page (but disable auto_navigate to avoid loops)
                result = scrape_url(leadership_url, auto_navigate=False)
                # Mark that we navigated from the original URL
                result['navigated_from'] = url
                return result
        
        # Extract metadata
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title"
        
        # Store original HTML before cleaning
        original_html = str(soup)
        
        # Remove script and style elements for text extraction
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get text content while preserving some structure
        text_content = soup.get_text(separator='\n', strip=True)
        lines = (line.strip() for line in text_content.splitlines() if line.strip())
        text = '\n'.join(lines)
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            img_src = img.get('src', '')
            img_alt = img.get('alt', '')
            if img_src:
                img_url = urljoin(url, img_src)
                images.append({
                    'url': img_url,
                    'alt': img_alt
                })
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            link_url = urljoin(url, link['href'])
            link_text = link.get_text().strip()
            if link_text:
                links.append({
                    'url': link_url,
                    'text': link_text
                })
        
        result = {
            'url': url,
            'title': title_text,
            'text': text[:5000],  # Limit text length for display
            'full_text': text,
            'images': images[:50],  # Limit images
            'links': links[:100],  # Limit links
            'scraped_at': datetime.now().isoformat(),
            'html': original_html,  # Store FULL HTML for complete parsing
            'navigated_from': None  # Will be set if auto-navigated
        }
        
        logger.success(f"Successfully scraped {url}: {len(text)} chars, {len(images)} images")
        return result
        
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {e}")
        return {
            'url': url,
            'error': str(e),
            'scraped_at': datetime.now().isoformat()
        }


def extract_leadership_info(content: Dict[str, Any], extraction_query: str = "") -> List[Dict[str, Any]]:
    """
    Universal leadership extractor that works with any website structure.
    
    Extraction Strategies (in order of preference):
    1. Leadership sections with structured cards/profiles
    2. Heading-based extraction (h1-h6 with adjacent text)
    3. List-based extraction (ul/ol with name-title pairs)
    4. Table-based extraction
    5. Text pattern matching (fallback)
    
    Args:
        content: Scraped content dictionary with 'html', 'text', 'images', 'links', 'url'
        extraction_query: Optional specific extraction instructions
        
    Returns:
        List of dictionaries with keys: name, title, image_url, profile_url, source_url, context
    """
    leaders = []
    found_leaders = {}  # Track by name to avoid duplicates
    
    if 'error' in content:
        return leaders
    
    text = content.get('full_text', '')
    html = content.get('html', '')
    images = content.get('images', [])
    links = content.get('links', [])
    source_url = content.get('url', '')
    
    if not html or not text:
        logger.warning("No HTML or text content to extract from")
        return leaders
    
    soup = BeautifulSoup(html, 'html.parser')
    logger.info(f"Starting universal extraction from {source_url}")
    
    # Find leadership page links for suggestions
    leadership_page_links = []
    if links:
        for link in links:
            link_text = link.get('text', '').lower()
            link_url = link.get('url', '').lower()
            if any(keyword in link_text or keyword in link_url 
                   for keyword in ['leadership', 'our-team', 'team', 'management', 'executive', 'about-us']):
                if link.get('url') and link.get('url') not in leadership_page_links:
                    leadership_page_links.append(link.get('url'))
    
    # ============================================================================
    # CONFIGURATION: Leadership titles and patterns
    # ============================================================================
    
    leadership_titles = {
        # C-Level (Priority 10)
        'ceo': 10, 'chief executive officer': 10, 'chief executive': 10,
        'cto': 10, 'chief technology officer': 10, 'chief technical officer': 10,
        'cfo': 10, 'chief financial officer': 10,
        'coo': 10, 'chief operating officer': 10,
        'cmo': 9, 'chief marketing officer': 9,
        'cio': 9, 'chief information officer': 9,
        'cso': 9, 'chief security officer': 9,
        'cdo': 9, 'chief data officer': 9,
        'cpo': 9, 'chief product officer': 9,
        'chief': 9,  # Generic chief
        
        # President/Founder (Priority 9)
        'president': 9, 'vice president': 8, 'vp': 8,
        'founder': 9, 'co-founder': 9, 'cofounder': 9,
        'chairman': 9, 'chairwoman': 9, 'chair': 9,
        
        # Directors (Priority 7-8)
        'managing director': 8, 'executive director': 8,
        'director': 7, 'associate director': 6,
        
        # Heads (Priority 6-7)
        'head of': 7, 'department head': 7,
        
        # Managers (Priority 5-6)
        'senior manager': 6, 'manager': 5,
        'program manager': 5, 'project manager': 5,
        
        # Others (Priority 4-5)
        'partner': 6, 'principal': 6,
        'architect': 5, 'lead': 5, 'senior': 4
    }
    
    # Section keywords for leadership
    leadership_section_keywords = [
        'leadership', 'team', 'management', 'executive', 
        'our team', 'meet the team', 'about us', 'who we are',
        'our people', 'board', 'founders', 'staff'
    ]
    
    # Testimonial keywords to avoid
    testimonial_keywords = [
        'testimonial', 'review', 'customer', 'client', 
        'feedback', 'what people say', 'success story'
    ]
    
    def is_testimonial_section(element):
        """Check if an element is part of testimonials."""
        elem_text = element.get_text().lower()[:500]
        elem_class = ' '.join(element.get('class', [])).lower()
        return any(kw in elem_text or kw in elem_class for kw in testimonial_keywords)
    
    def calculate_priority(title_text: str) -> int:
        """Calculate priority score for a title."""
        title_lower = title_text.lower()
        max_priority = 0
        for keyword, priority in leadership_titles.items():
            if keyword in title_lower:
                max_priority = max(max_priority, priority)
        return max_priority
    
    def is_valid_name(name: str) -> bool:
        """Validate if a string looks like a person's name."""
        if not name or len(name) < 3:
            return False
        
        parts = name.split()
        if not (2 <= len(parts) <= 5):  # Most names are 2-5 words
            return False
        
        # Check if words start with capital letters
        if not all(part[0].isupper() or part[0].isdigit() for part in parts if part):
            return False
        
        # Avoid obviously wrong patterns
        if len(name) > 100 or any(char in name for char in ['@', 'http', '|', '>']):
            return False
        
        return True
    
    def clean_title(title: str) -> str:
        """Clean and normalize a title."""
        # Remove extra whitespace and newlines
        title = ' '.join(title.split())
        # Limit length
        title = title[:150]
        # Remove trailing/leading punctuation
        title = title.strip(',.;:- ')
        return title
    
    def find_image_for_person(person_element, name_parts):
        """Find the most relevant image for a person."""
        # Look for img in the same container
        img = person_element.find('img')
        if img and img.get('src'):
            return urljoin(source_url, img['src'])
        
        # Look in images list by alt text or filename
        for img_dict in images:
            img_alt = img_dict.get('alt', '').lower()
            img_url = img_dict.get('url', '').lower()
            if any(part.lower() in img_alt or part.lower() in img_url for part in name_parts):
                return img_dict.get('url')
        
        return None
    
    def add_leader(name, title, image_url=None, profile_url=None, context='extracted'):
        """Add a leader to the found_leaders dict if valid."""
        if not is_valid_name(name):
            return False
        
        priority = calculate_priority(title)
        if priority == 0:
            # Title doesn't match leadership keywords
            return False
        
        title = clean_title(title)
        
        # Add or update if higher priority
        if name not in found_leaders or found_leaders[name]['priority'] < priority:
            found_leaders[name] = {
                'name': name,
                'title': title,
                'priority': priority,
                'image_url': image_url,
                'profile_url': profile_url,
                'source_url': source_url,
                'extraction_context': context,
                'extracted_at': datetime.now().isoformat()
            }
            logger.debug(f"Added: {name} - {title} (priority: {priority})")
            return True
        return False
    
    # ============================================================================
    # STRATEGY 0: Link-based extraction (WordPress/Elementor style)
    # ============================================================================
    
    logger.info("Strategy 0: Looking for leadership profile links...")
    
    # Find links to individual leadership pages
    leadership_links = []
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        link_text = link.get_text().strip()
        
        # Convert relative URLs to absolute
        full_href = urljoin(source_url, href)
        
        # Check if link goes to individual leadership profile
        leadership_patterns = ['/leadership/', '/team/', '/people/', '/staff/', '/executives/', '/about/']
        if any(pattern in full_href.lower() for pattern in leadership_patterns):
            # Check if href has individual profile structure (ends with a name-like segment)
            # Must have at least 4 slashes for individual profiles
            if full_href.count('/') >= 4 or href.count('/') >= 3:
                # Validate that link text looks like a name
                if link_text and is_valid_name(link_text):
                    leadership_links.append({
                        'name': link_text,
                        'url': full_href,
                        'element': link
                    })
    
    logger.info(f"Found {len(leadership_links)} leadership profile links")
    
    # Debug: Show first few links found
    if leadership_links:
        for i, lnk in enumerate(leadership_links[:3], 1):
            logger.debug(f"  {i}. {lnk['name'][:30]} -> {lnk['url'][:60]}")
    
    # Extract from each leader link
    for link_data in leadership_links:
        name = link_data['name']
        profile_url = link_data['url']
        link_elem = link_data['element']
        
        # Validate name
        if not is_valid_name(name):
            continue
        
        # Skip if already found
        if name in found_leaders:
            continue
        
        # Find parent container to get image
        parent = link_elem.find_parent(['div', 'article', 'li'])
        photo_url = None
        
        if parent:
            # Look for image in parent container
            img = parent.find('img')
            if img:
                # Try multiple attributes for lazy loading
                img_src = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          img.get('srcset', '').split(',')[0].split()[0] if img.get('srcset') else None)
                if img_src and not img_src.startswith('data:'):  # Skip data URLs
                    photo_url = urljoin(source_url, img_src)
        
        # If no image in parent, check if link contains an image
        if not photo_url:
            img = link_elem.find('img')
            if img:
                # Try multiple attributes for lazy loading
                img_src = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          img.get('srcset', '').split(',')[0].split()[0] if img.get('srcset') else None)
                if img_src and not img_src.startswith('data:'):  # Skip data URLs
                    photo_url = urljoin(source_url, img_src)
        
        # Try to extract title from nearby text or profile page
        title = "Leadership Team Member"  # Default title
        
        # Look for title in parent or nearby elements
        if parent:
            # Strategy 1: Look for elements with title-related classes
            title_elem = parent.find(['p', 'span', 'div', 'h3', 'h4', 'h5'], 
                                    class_=re.compile(r'(title|position|role|designation|job)', re.I))
            if title_elem:
                extracted_title = clean_title(title_elem.get_text().strip())
                if extracted_title and len(extracted_title) > 3:
                    title = extracted_title
            
            # Strategy 2: Look for any p, span, or div that comes after the name
            if title == "Leadership Team Member":
                # Find all text elements in parent
                text_elements = parent.find_all(['p', 'span', 'div', 'h3', 'h4'])
                for elem in text_elements:
                    text = elem.get_text().strip()
                    # Skip if it's the name itself
                    if text == name or name in text:
                        continue
                    # Check if it looks like a title (not too long, not empty)
                    if text and 5 < len(text) < 80 and not text.startswith('http'):
                        # Avoid common non-title text
                        if not any(skip in text.lower() for skip in ['read more', 'learn more', 'view profile', 'linkedin', 'email', 'phone']):
                            extracted_title = clean_title(text)
                            if extracted_title and len(extracted_title) > 3:
                                title = extracted_title
                                break
            
            # Strategy 3: Look for sibling elements
            if title == "Leadership Team Member":
                # Check next sibling of the link
                next_elem = link_elem.find_next_sibling(['p', 'span', 'div'])
                if next_elem:
                    text = next_elem.get_text().strip()
                    if text and 5 < len(text) < 80:
                        extracted_title = clean_title(text)
                        if extracted_title and len(extracted_title) > 3:
                            title = extracted_title
        
        # Add the leader
        # If title is still default, try to fetch from profile page
        if title == "Leadership Team Member" and profile_url:
            try:
                resp = requests.get(profile_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    profile_soup = BeautifulSoup(resp.text, "html.parser")
                    # Try h1-h4, strong, b, or first large text block
                    title_tag = profile_soup.find(["h1", "h2", "h3", "h4", "strong", "b"], string=True)
                    if title_tag:
                        possible_title = title_tag.get_text().strip()
                        # Avoid using the name as title
                        if possible_title and possible_title != name and 3 < len(possible_title) < 80:
                            title = possible_title
                    # Fallback: look for first large text block
                    if title == "Leadership Team Member":
                        for tag in profile_soup.find_all(["p", "span", "div"]):
                            txt = tag.get_text().strip()
                            if txt and txt != name and 3 < len(txt) < 80 and not txt.startswith("http"):
                                if not any(skip in txt.lower() for skip in ["read more", "learn more", "view profile", "linkedin", "email", "phone"]):
                                    title = txt
                                    break
            except Exception as e:
                logger.warning(f"Failed to fetch profile page for {name}: {e}")
        if add_leader(name, title, photo_url, profile_url, "link-based"):
            logger.info(f"  ✓ Extracted from link: {name} -> {profile_url}")
    
    # ============================================================================
    # STRATEGY 1: Find leadership sections and extract from structured elements
    # ============================================================================
    
    logger.info("Strategy 1: Looking for leadership sections...")
    
    # Find sections with leadership-related classes or IDs
    leadership_sections = []
    
    for tag in ['section', 'div', 'article']:
        sections = soup.find_all(tag)
        for section in sections:
            section_class = ' '.join(section.get('class', [])).lower()
            section_id = section.get('id', '').lower()
            section_text = section.get_text()[:200].lower()
            
            # Check if this looks like a leadership section
            is_leadership = any(kw in section_class or kw in section_id or kw in section_text 
                               for kw in leadership_section_keywords)
            
            # Skip testimonials
            is_testimonial = is_testimonial_section(section)
            
            if is_leadership and not is_testimonial:
                leadership_sections.append(section)
                logger.info(f"Found leadership section: {tag} with class='{section_class[:50]}'")
    
    # Extract from leadership sections
    for section in leadership_sections:
        # Look for individual profile cards/items
        cards = section.find_all(['div', 'li', 'article'], class_=re.compile(
            r'(card|member|person|profile|bio|item|box)', re.I))
        
        if not cards:
            # If no specific cards, look for any divs/lis
            cards = section.find_all(['div', 'li'])[:50]  # Limit to avoid processing too many
        
        for card in cards:
            # Skip if looks like testimonial
            if is_testimonial_section(card):
                continue
            
            # Try to extract name (usually in heading tags)
            name = None
            name_tag = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
            
            if name_tag:
                name = ' '.join(name_tag.get_text().split())
                
                if is_valid_name(name):
                    # Extract title (text after name)
                    title = None
                    
                    # Method 1: Check immediate next siblings
                    for sibling in list(name_tag.next_siblings)[:5]:
                        if isinstance(sibling, str):
                            text = sibling.strip()
                            if text and 3 < len(text) < 200:  # Relaxed minimum from 10 to 3
                                title = text
                                break
                        elif hasattr(sibling, 'name') and sibling.name in ['p', 'span', 'div', 'h5', 'h6']:
                            text = sibling.get_text().strip()
                            if text and 3 < len(text) < 200:  # Relaxed minimum from 10 to 3
                                title = text
                                break
                    
                    # Method 2: Look for elements with title-related classes
                    if not title:
                        title_elem = card.find(['p', 'span', 'div', 'h5', 'h6'], class_=re.compile(
                            r'(title|position|role|job|designation)', re.I))
                        if title_elem:
                            title = title_elem.get_text().strip()
                    
                    # Method 3: Extract from card text (get text after name)
                    if not title:
                        card_text = card.get_text()
                        if name in card_text:
                            after_name = card_text.split(name, 1)[1].strip()
                            lines = [l.strip() for l in after_name.split('\n') if l.strip()]
                            for line in lines[:3]:
                                if 3 < len(line) < 200:  # Relaxed minimum from 10 to 3
                                    title = line
                                    break
                    
                    if title:
                        # Find image
                        name_parts = name.split()
                        image_url = find_image_for_person(card, name_parts)
                        
                        # Find profile link
                        profile_url = None
                        link = name_tag.find('a') or card.find('a')
                        if link and link.get('href'):
                            profile_url = urljoin(source_url, link['href'])
                        
                        add_leader(name, title, image_url, profile_url, 'leadership_section')
    
    # ============================================================================
    # STRATEGY 2: Heading-based extraction (all h1-h6 tags)
    # ============================================================================
    
    if len(found_leaders) < 5:
        logger.info("Strategy 2: Heading-based extraction...")
        
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            # Skip if in testimonial section
            parent = heading.find_parent(['section', 'div', 'article'])
            if parent and is_testimonial_section(parent):
                continue
            
            name = ' '.join(heading.get_text().split())
            
            if is_valid_name(name):
                # Get title from next elements
                title = None
                for sibling in list(heading.next_siblings)[:5]:
                    if isinstance(sibling, str):
                        text = sibling.strip()
                        if text and 3 < len(text) < 200:  # Relaxed minimum from 10 to 3
                            title = text
                            break
                    elif hasattr(sibling, 'name'):
                        if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            break  # Hit next heading
                        text = sibling.get_text().strip()
                        if text and 3 < len(text) < 200:  # Relaxed minimum from 10 to 3
                            title = text
                            break
                
                if title:
                    name_parts = name.split()
                    container = heading.find_parent(['div', 'article', 'section', 'li'])
                    image_url = find_image_for_person(container or heading, name_parts) if container else None
                    
                    link = heading.find('a')
                    profile_url = None
                    if link and link.get('href'):
                        profile_url = urljoin(source_url, link['href'])
                    
                    add_leader(name, title, image_url, profile_url, 'heading_extraction')
    
    # ============================================================================
    # STRATEGY 3: Text pattern matching (fallback)
    # ============================================================================
    
    if len(found_leaders) < 3:
        logger.info("Strategy 3: Text pattern matching...")
        
        patterns = [
            # Name followed by newline and title
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z\'\.]+){1,4})\s*\n\s*([A-Z][^|\n]{3,150})',  # Relaxed minimum from 10 to 3
            # Name with dash or comma and title
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z\'\.]+){1,4})\s*[-–—,]\s*([A-Z][^|\n]{3,150})',  # Relaxed minimum from 10 to 3
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                title = match.group(2).strip()
                
                # Clean up title
                title = title.split('\n')[0]  # Take first line only
                
                if is_valid_name(name) and calculate_priority(title) > 0:
                    add_leader(name, title, None, None, 'text_pattern')
    
    # ============================================================================
    # FINALIZE: Convert to list and sort
    # ============================================================================
    
    leaders = list(found_leaders.values())
    
    # Sort by priority (highest first)
    leaders.sort(key=lambda x: x['priority'], reverse=True)
    
    # Remove priority field (internal use only)
    for leader in leaders:
        leader.pop('priority', None)
    
    # Add suggestion for better URLs if found few results
    if len(leaders) < 5 and leadership_page_links:
        content['suggested_leadership_urls'] = leadership_page_links[:5]
        logger.warning(f"Only found {len(leaders)} leaders. Suggested URLs: {leadership_page_links[:3]}")
    
    logger.success(f"Extracted {len(leaders)} unique leadership profiles")
    return leaders


def save_leaders_to_db(leaders: List[Dict[str, Any]]) -> int:
    """
    Save extracted leaders to SQLite database.
    
    Args:
        leaders: List of leader dictionaries
        
    Returns:
        Number of leaders saved
    """
    if not leaders:
        return 0
    
    db_session = st.session_state.db_session
    saved_count = 0
    
    with db_session.get_session() as session:
        profile_repo = ProfileRepository(session)
        
        for leader in leaders:
            try:
                # Create or update profile
                profile = profile_repo.create_profile(
                    name=leader['name'],
                    source_url=leader.get('source_url', ''),
                    title=leader.get('title'),
                    photo_url=leader.get('image_url'),
                    confidence_score=0.8,  # Default confidence
                    source="url_scraper",
                    metadata=json.dumps({
                        'extracted_at': leader.get('extracted_at'),
                        'extraction_method': 'pattern_matching'
                    })
                )
                
                if profile:
                    saved_count += 1
                    logger.info(f"Saved leader: {leader['name']}")
                
            except Exception as e:
                logger.error(f"Error saving leader {leader.get('name')}: {e}")
    
    return saved_count


# ============================================================================
# CHAT INTERFACE COMPONENTS
# ============================================================================

def display_url_input_section():
    """Display URL input section."""
    st.markdown("### 🌐 Enter URL to Analyze")
    
    st.info("💡 **Smart Navigation**: Just enter the homepage! The system will automatically find and navigate to the leadership/team page.")
    
    with st.form(key="url_input_form"):
        url_input = st.text_input(
            "Website URL:",
            placeholder="https://amzur.com (homepage works too!)",
            help="Enter any company URL - the system will automatically find the leadership page"
        )
        
        auto_nav = st.checkbox(
            "🔄 Auto-navigate to leadership page",
            value=True,
            help="Automatically find and navigate to the leadership/team page from homepage"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            scrape_button = st.form_submit_button("🔍 Scrape URL", use_container_width=True, type="primary")
        
        if scrape_button and url_input:
            # Validate URL
            if not validators.url(url_input):
                st.error("❌ Invalid URL. Please enter a valid URL starting with http:// or https://")
                return
            
            # Scrape the URL
            with st.spinner(f"🔄 Scraping {url_input}..."):
                # Show navigation status if auto_nav is enabled
                if auto_nav:
                    st.info("🔍 Looking for leadership page...")
                
                content = scrape_url(url_input, auto_navigate=auto_nav)
                
                if 'error' in content:
                    st.error(f"❌ Error scraping URL: {content['error']}")
                else:
                    st.session_state.current_url = url_input
                    st.session_state.scraped_content = content
                    
                    # Show success message with navigation info
                    if content.get('navigated_from'):
                        st.success(f"✅ Found and scraped leadership page!")
                        st.info(f"🔄 Navigated from: {content['navigated_from']}\n\n📍 Now viewing: {content['url']}")
                    else:
                        st.success(f"✅ Successfully scraped: {content['title']}")
                    
                    st.rerun()


def display_scraped_content():
    """Display scraped content summary."""
    if not st.session_state.scraped_content:
        return
    
    content = st.session_state.scraped_content
    
    st.markdown("### 📄 Scraped Content")
    
    # Show navigation info if we auto-navigated
    if content.get('navigated_from'):
        st.success(f"✅ **Auto-navigated to leadership page**")
        st.markdown(f"🏠 Started from: `{content['navigated_from']}`")
        st.markdown(f"📍 Leadership page: `{content['url']}`")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Text Length", f"{len(content.get('full_text', ''))} chars")
    with col2:
        st.metric("Images Found", len(content.get('images', [])))
    with col3:
        st.metric("Links Found", len(content.get('links', [])))
    
    with st.expander("📝 View Content Preview", expanded=False):
        st.markdown(f"**Title:** {content.get('title')}")
        st.markdown(f"**URL:** {content.get('url')}")
        st.markdown("**Text Preview:**")
        st.text_area("Content", content.get('text', ''), height=200, disabled=True)


def display_extraction_actions():
    """Display extraction action buttons."""
    if not st.session_state.scraped_content:
        return
    
    st.markdown("### 🎯 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👥 Extract Leadership", use_container_width=True):
            with st.spinner("Extracting leadership information..."):
                leaders = extract_leadership_info(st.session_state.scraped_content)
                st.session_state.extracted_leaders = leaders
                
                if leaders:
                    st.success(f"✅ Extracted {len(leaders)} leaders")
                    # Show what was found
                    st.info(f"📋 Found: {', '.join([l['name'] for l in leaders[:5]])}" + 
                           (f" and {len(leaders)-5} more..." if len(leaders) > 5 else ""))
                else:
                    st.warning("⚠️ No leadership information found")
                st.rerun()
    
    with col2:
        if st.button("💾 Save to Database", use_container_width=True):
            if st.session_state.extracted_leaders:
                saved = save_leaders_to_db(st.session_state.extracted_leaders)
                st.success(f"✅ Saved {saved} leaders to database")
            else:
                st.warning("⚠️ No leaders to save. Extract leadership first.")
    
    with col3:
        if st.button("� Load JSON", use_container_width=True):
            try:
                import json
                with open('amzur_leadership.json', 'r', encoding='utf-8') as f:
                    leaders = json.load(f)
                    st.session_state.extracted_leaders = leaders
                    st.success(f"✅ Loaded {len(leaders)} leaders from JSON")
                    st.rerun()
            except FileNotFoundError:
                st.error("❌ amzur_leadership.json not found. Run test_amzur_extractor.py first")
            except Exception as e:
                st.error(f"❌ Error loading JSON: {e}")
    
    with col4:
        if st.button("�🔄 Clear Data", use_container_width=True):
            st.session_state.scraped_content = None
            st.session_state.extracted_leaders = []
            st.session_state.current_url = None
            st.success("✅ Data cleared")
            st.rerun()


def display_extracted_leaders():
    """Display extracted leadership information with better formatting."""
    if not st.session_state.extracted_leaders:
        return
    
    st.markdown("### 👥 Extracted Leadership")
    st.caption(f"Found {len(st.session_state.extracted_leaders)} leaders (sorted by relevance)")
    
    # Add option to filter or review
    col1, col2 = st.columns([3, 1])
    with col1:
        show_all = st.checkbox("Show all extracted data", value=False)
    with col2:
        if st.button("🗑️ Clear Results"):
            st.session_state.extracted_leaders = []
            st.rerun()
    
    for idx, leader in enumerate(st.session_state.extracted_leaders, 1):
        with st.container():
            # Create a card-like display
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                if leader.get('image_url'):
                    try:
                        st.image(leader['image_url'], width=80)
                    except:
                        st.markdown("�")
                else:
                    st.markdown("### 👤")
            
            with col2:
                st.markdown(f"**{idx}. {leader['name']}**")
                st.caption(f"📋 {leader.get('title', 'No title')}")
                
                if show_all:
                    st.caption(f"🔗 Source: {leader.get('source_url', 'N/A')}")
                    if leader.get('image_url'):
                        st.caption(f"�️ [Image URL]({leader['image_url']})")
                    st.caption(f"⏰ Extracted: {leader.get('extracted_at', 'N/A')[:19]}")
            
            with col3:
                # Show confidence score instead of selection checkbox
                confidence = leader.get('confidence_score', 0)
                if confidence > 0:
                    st.caption(f"🎯 {confidence}%")
            
            st.markdown("---")


def display_chat_interface():
    """Display chat interface for asking questions."""
    if not st.session_state.scraped_content:
        st.info("👆 Enter a URL above to start analyzing content")
        return
    
    st.markdown("### 💬 Ask Questions")
    
    # Display messages
    for msg in st.session_state.messages:
        role = msg['role']
        content = msg['content']
        
        if role == 'user':
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br/>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render assistant message with readable color
            st.markdown(f"""
            <div style='color: #e0e0e0; background: #222; padding: 12px 18px; border-radius: 8px; margin-bottom: 8px;'>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        user_query = st.text_area(
            "Your Question:",
            placeholder="Ask about the content, e.g., 'Who are the leaders?' or 'Extract all email addresses'",
            height=100
        )
        
        submit_button = st.form_submit_button("💬 Ask", use_container_width=True, type="primary")
        
        if submit_button and user_query:
            handle_chat_query(user_query)
            st.rerun()


def handle_chat_query(query: str):
    """
    Handle user chat query.
    
    Args:
        query: User's question
    """
    # Add user message
    st.session_state.messages.append({
        'role': 'user',
        'content': query
    })
    
    # Generate response based on scraped content
    content = st.session_state.scraped_content
    
    # Simple rule-based responses for common queries
    query_lower = query.lower()
    response = ""
    
    if any(word in query_lower for word in ['leader', 'leadership', 'ceo', 'executive', 'management']):
        if not st.session_state.extracted_leaders:
            # Extract leaders
            leaders = extract_leadership_info(content)
            st.session_state.extracted_leaders = leaders
        
        if st.session_state.extracted_leaders:
            leader_list = "\n".join([f"- **{l['name']}**: {l.get('title', 'No title')}" 
                                      for l in st.session_state.extracted_leaders])
            response = f"I found {len(st.session_state.extracted_leaders)} leaders:\n\n{leader_list}"
        else:
            response = "I couldn't find any leadership information on this page."
    
    elif any(word in query_lower for word in ['image', 'photo', 'picture']):
        images = content.get('images', [])
        if images:
            image_list = "\n".join([f"- {img.get('alt', 'No description')}: {img['url']}" 
                                     for img in images[:10]])
            response = f"I found {len(images)} images. Here are the first 10:\n\n{image_list}"
        else:
            response = "No images found on this page."
    
    elif any(word in query_lower for word in ['email', 'contact']):
        text = content.get('full_text', '')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            email_list = "\n".join([f"- {email}" for email in set(emails)])
            response = f"I found {len(set(emails))} email addresses:\n\n{email_list}"
        else:
            response = "No email addresses found on this page."
    
    elif any(word in query_lower for word in ['phone', 'telephone', 'number']):
        text = content.get('full_text', '')
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        if phones:
            phone_list = "\n".join([f"- {phone}" for phone in set(phones)])
            response = f"I found {len(set(phones))} phone numbers:\n\n{phone_list}"
        else:
            response = "No phone numbers found on this page."
    
    elif any(word in query_lower for word in ['save', 'store', 'database']):
        if st.session_state.extracted_leaders:
            saved = save_leaders_to_db(st.session_state.extracted_leaders)
            response = f"✅ Saved {saved} leaders to the database."
        else:
            response = "No leaders have been extracted yet. Please extract leadership information first."
    
    else:
        # General response about the content
        title = content.get('title', 'this page')
        text_length = len(content.get('full_text', ''))
        image_count = len(content.get('images', []))
        response = f"I've analyzed **{title}**. The page contains {text_length} characters and {image_count} images. You can ask me to extract leadership, images, emails, or phone numbers."
    
    # Add assistant message
    st.session_state.messages.append({
        'role': 'assistant',
        'content': response
    })


# ============================================================================
# SIDEBAR
# ============================================================================

def display_sidebar():
    """Display sidebar with information."""
    with st.sidebar:
        st.title("🌐 URL Knowledge Chat")
        
        st.markdown("### 📊 Session Info")
        st.info(f"**Session:** `{st.session_state.session_id[:20]}...`")
        
        if st.session_state.current_url:
            st.success(f"**Current URL:**\n{st.session_state.current_url}")
        
        st.metric("Messages", len(st.session_state.messages))
        st.metric("Extracted Leaders", len(st.session_state.extracted_leaders))
        
        st.markdown("---")
        st.markdown("### 💡 How to Use")
        st.markdown("""
        1. **Enter URL**: Paste the website URL
        2. **Scrape**: Click "Scrape URL"
        3. **Extract**: Click "Extract Leadership"
        4. **Save**: Click "Save to Database"
        5. **Ask**: Ask questions about the content
        
        **Example Questions:**
        - "Who are the leaders?"
        - "Extract all images"
        - "Find email addresses"
        - "Show phone numbers"
        - "Save to database"
        """)
        
        st.markdown("---")
        st.markdown("### 📂 Database")
        
        db_session = st.session_state.db_session
        
        try:
            with db_session.get_session() as session:
                profile_repo = ProfileRepository(session)
                profile_count = profile_repo.count()
                st.metric("Total Profiles", profile_count)
        except Exception as e:
            st.error(f"Database error: {e}")
            st.metric("Total Profiles", "Error")
        
        if st.button("🗑️ Clear Database", use_container_width=True):
            st.warning("⚠️ Clear database functionality requires confirmation")


# ============================================================================
# ENHANCED LEADER DISPLAY
# ============================================================================

def display_leader_cards():
    """Display leaders in a beautiful card grid with photos."""
    if not st.session_state.extracted_leaders:
        return
    
    st.markdown("### 👥 Leadership Team")
    st.caption(f"✨ Found {len(st.session_state.extracted_leaders)} leaders")
    
    # Debug: Show raw data to troubleshoot image issues
    with st.expander("🔍 Debug: View Raw Extracted Data"):
        st.caption(f"Showing data for all {len(st.session_state.extracted_leaders)} leaders")
        for i, leader in enumerate(st.session_state.extracted_leaders, 1):
            st.markdown(f"**{i}. {leader.get('name')}**")
            st.json({
                'name': leader.get('name'),
                'title': leader.get('title'),
                'image_url': leader.get('image_url'),
                'photo_url': leader.get('photo_url'),
                'profile_url': leader.get('profile_url'),
                'extraction_context': leader.get('extraction_context'),
                'priority': leader.get('priority'),
            })
            st.markdown("---")
    
    # Display leaders in grid - 3 per row
    leaders = st.session_state.extracted_leaders
    
    for row_start in range(0, len(leaders), 3):
        cols = st.columns(3)
        
        for col_idx in range(3):
            idx = row_start + col_idx
            if idx >= len(leaders):
                break
            
            leader = leaders[idx]
            
            with cols[col_idx]:
                # Card container with custom styling
                st.markdown(f"""
                <div style="border: 1px solid #e0e0e0; 
                            border-radius: 10px; 
                            padding: 15px; 
                            background: white;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            margin-bottom: 20px;">
                """, unsafe_allow_html=True)
                
                # Photo - check both 'photo_url' and 'image_url'
                photo_url = leader.get('photo_url') or leader.get('image_url')
                
                if photo_url and photo_url.strip():
                    # Clean the URL
                    photo_url = photo_url.strip()
                    
                    # Check if it's a valid URL
                    if photo_url.startswith(('http://', 'https://', '//')):
                        try:
                            st.image(photo_url, use_container_width=True)
                        except Exception as e:
                            # Show error in debug mode
                            st.caption(f"⚠️ Image failed to load")
                            # Fallback placeholder
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        height: 250px; 
                                        display: flex; 
                                        align-items: center; 
                                        justify-content: center; 
                                        border-radius: 8px;">
                                <div style="font-size: 80px;">👤</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        # Invalid URL format
                        st.caption(f"⚠️ Invalid image URL")
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    height: 250px; 
                                    display: flex; 
                                    align-items: center; 
                                    justify-content: center; 
                                    border-radius: 8px;">
                            <div style="font-size: 80px;">👤</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # No photo - styled placeholder
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                height: 250px; 
                                display: flex; 
                                align-items: center; 
                                justify-content: center; 
                                border-radius: 8px;">
                        <div style="font-size: 80px;">👤</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Name
                name = leader.get('name', 'Unknown')
                st.markdown(f"### {name}")
                
                # Title
                title = leader.get('title', 'No title')
                st.markdown(f"**{title}**")
                
                # Profile link if available
                profile_url = leader.get('profile_url')
                if profile_url:
                    st.markdown(f"[🔗 View Full Profile]({profile_url})")
                
                # Confidence score
                confidence = leader.get('confidence_score', 0)
                if confidence > 0:
                    st.caption(f"⭐ Confidence: {confidence}/10")
                
                st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    configure_page()
    initialize_session_state()
    
    # Display sidebar
    display_sidebar()
    
    # Main content
    st.title("🌐 URL Knowledge Chat")
    st.markdown("*Scrape websites, extract information, and ask questions about the content*")
    
    # URL input section
    display_url_input_section()
    
    # Scraped content summary
    if st.session_state.scraped_content:
        display_scraped_content()
        
        # Extraction actions
        display_extraction_actions()
        
        # Display extracted leaders with beautiful cards
        if st.session_state.extracted_leaders:
            st.markdown("---")
            display_leader_cards()
            display_extracted_leaders()  # Keep old one for additional functionality
        
        # Chat interface
        st.markdown("---")
        display_chat_interface()


if __name__ == "__main__":
    main()
