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

def scrape_url(url: str) -> Dict[str, Any]:
    """
    Scrape content from a URL.
    
    Args:
        url: URL to scrape
        
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
            'html': original_html[:50000]  # Store more HTML for better parsing
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
    Extract leadership information from scraped content using improved pattern matching.
    
    Args:
        content: Scraped content dictionary
        extraction_query: Optional specific extraction instructions
        
    Returns:
        List of extracted leadership profiles
    """
    leaders = []
    
    if 'error' in content:
        return leaders
    
    text = content.get('full_text', '')
    html = content.get('html', '')
    images = content.get('images', [])
    links = content.get('links', [])
    soup = BeautifulSoup(html, 'html.parser') if html else None
    
    # First, check if this page has testimonials (not leadership)
    testimonial_indicators = ['testimonial', 'review', 'customer', 'client', 'feedback', 'quote']
    is_testimonial_page = any(indicator in text.lower() for indicator in testimonial_indicators)
    
    # Look for dedicated leadership page links
    leadership_page_links = []
    if links:
        for link in links:
            link_text = link.get('text', '').lower()
            link_url = link.get('url', '').lower()
            if any(keyword in link_text or keyword in link_url 
                   for keyword in ['leadership', 'team', 'management', 'executive', 'about us']):
                leadership_page_links.append(link.get('url'))
    
    # If we detect this might be testimonials, set a flag
    extracted_from_testimonials = False
    
    # Common leadership titles with priority
    leadership_titles = {
        'ceo': ('Chief Executive Officer', 10),
        'chief executive officer': ('Chief Executive Officer', 10),
        'president': ('President', 9),
        'founder': ('Founder', 9),
        'co-founder': ('Co-Founder', 9),
        'cofounder': ('Co-Founder', 9),
        'chairman': ('Chairman', 8),
        'chairwoman': ('Chairwoman', 8),
        'chair': ('Chair', 8),
        'cto': ('Chief Technology Officer', 8),
        'chief technology officer': ('Chief Technology Officer', 8),
        'cfo': ('Chief Financial Officer', 8),
        'chief financial officer': ('Chief Financial Officer', 8),
        'coo': ('Chief Operating Officer', 8),
        'chief operating officer': ('Chief Operating Officer', 8),
        'cmo': ('Chief Marketing Officer', 7),
        'chief marketing officer': ('Chief Marketing Officer', 7),
        'vice president': ('Vice President', 7),
        'vp': ('Vice President', 7),
        'director': ('Director', 6),
        'managing director': ('Managing Director', 7),
        'head of': ('Head of', 6),
        'partner': ('Partner', 6),
        'executive': ('Executive', 5)
    }
    
    # Track found leaders to avoid duplicates
    found_leaders = {}  # key: name, value: (title, priority, image_url, context)
    
    # Strategy 1: Look for structured HTML elements (most reliable)
    if soup:
        # Look for leadership-specific sections FIRST (not testimonials)
        leadership_sections = soup.find_all(['div', 'section'], 
            class_=re.compile(r'(leadership|executive|management|founder|board|team\-member|our\-team)', re.I))
        
        # Exclude testimonial sections
        leadership_sections = [
            section for section in leadership_sections
            if not any(indicator in str(section.get('class', [])).lower() 
                      for indicator in testimonial_indicators)
        ]
        
        # If we found leadership sections, use them
        if leadership_sections:
            for section in leadership_sections:
                # Look for name-title pairs within cards or list items
                cards = section.find_all(['div', 'li', 'article'], 
                    class_=re.compile(r'(card|member|person|profile|bio)', re.I))
                
                for card in cards:
                    # Skip if this looks like a testimonial
                    card_text = card.get_text().lower()
                    if any(indicator in card_text for indicator in ['testimonial', 'customer', 'client says', 'review']):
                        continue
                    
                    # Try to find name (usually in h2, h3, h4, or strong tags)
                    name_tag = card.find(['h2', 'h3', 'h4', 'h5', 'strong', 'b'])
                    if name_tag:
                        name = name_tag.get_text().strip()
                        
                        # Clean up name (remove extra whitespace, newlines)
                        name = ' '.join(name.split())
                        
                        # Validate name (should be 2-4 words, proper capitalization)
                        name_parts = name.split()
                        if 2 <= len(name_parts) <= 4 and all(part[0].isupper() for part in name_parts if part):
                            # Look for title (usually in p, span, or div with class)
                            title_tag = card.find(['p', 'span', 'div'], 
                                class_=re.compile(r'(title|position|role|job)', re.I))
                            
                            if not title_tag:
                                # Try to find any text after the name
                                title_tag = card.find(['p', 'span', 'div'])
                            
                            if title_tag:
                                title = title_tag.get_text().strip()
                                title = ' '.join(title.split())
                                
                                # Check if title matches leadership keywords
                                title_lower = title.lower()
                                matched_title = None
                                max_priority = 0
                                
                                for keyword, (formal_title, priority) in leadership_titles.items():
                                    if keyword in title_lower:
                                        if priority > max_priority:
                                            matched_title = title  # Keep original title
                                            max_priority = priority
                                
                                if matched_title and max_priority > 0:
                                    # Try to find image
                                    img_tag = card.find('img')
                                    image_url = None
                                    if img_tag and img_tag.get('src'):
                                        from urllib.parse import urljoin
                                        image_url = urljoin(content.get('url', ''), img_tag['src'])
                                    
                                    # Add or update if higher priority
                                    if name not in found_leaders or found_leaders[name][1] < max_priority:
                                        found_leaders[name] = (matched_title, max_priority, image_url, 'leadership_section')
        
        # If no dedicated leadership sections, check all sections but mark them
        if not found_leaders:
            all_sections = soup.find_all(['div', 'section'])
            for section in all_sections:
                section_text = section.get_text().lower()
                
                # Skip obvious testimonial sections
                if any(indicator in section_text[:200] for indicator in ['testimonial', 'what our clients', 'customer review', 'client feedback']):
                    continue
                
                cards = section.find_all(['div', 'li', 'article'])
                for card in cards:
                    card_classes = ' '.join(card.get('class', [])).lower()
                    card_text = card.get_text().lower()
                    
                    # Skip testimonials
                    if 'testimonial' in card_classes or any(indicator in card_text[:100] for indicator in testimonial_indicators):
                        continue
                    
                    name_tag = card.find(['h2', 'h3', 'h4', 'h5'])
                    if name_tag:
                        name = ' '.join(name_tag.get_text().split())
                        name_parts = name.split()
                        
                        if 2 <= len(name_parts) <= 4 and all(part[0].isupper() for part in name_parts if part):
                            # Look for title
                            following_text = []
                            for sibling in name_tag.find_next_siblings(['p', 'span', 'div']):
                                text = sibling.get_text().strip()
                                if text and len(text) < 100:
                                    following_text.append(text)
                                if len(following_text) >= 2:
                                    break
                            
                            for title in following_text:
                                title_lower = title.lower()
                                matched_title = None
                                max_priority = 0
                                
                                for keyword, (formal_title, priority) in leadership_titles.items():
                                    if keyword in title_lower:
                                        if priority > max_priority:
                                            matched_title = title
                                            max_priority = priority
                                
                                if matched_title and max_priority > 0:
                                    img_tag = card.find('img')
                                    image_url = None
                                    if img_tag and img_tag.get('src'):
                                        from urllib.parse import urljoin
                                        image_url = urljoin(content.get('url', ''), img_tag['src'])
                                    
                                    # Mark that this might be from testimonials
                                    context = 'testimonial' if is_testimonial_page else 'general_page'
                                    extracted_from_testimonials = True
                                    
                                    if name not in found_leaders or found_leaders[name][1] < max_priority:
                                        found_leaders[name] = (matched_title, max_priority, image_url, context)
                                    break
    
    # Strategy 2: Pattern matching in plain text (fallback)
    if len(found_leaders) < 3:
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z\']+){1,3})\s*\n\s*([A-Z][a-zA-Z\s&,]+?)(?=\n|$)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z\']+){1,3})\s*[-–—,]\s*([A-Z][a-zA-Z\s&,]+?)(?=\n|\.|$)',
            r'([A-Z][a-zA-Z\s&,]+?):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z\']+){1,3})(?=\n|\.|$)',
        ]
        
        for pattern_idx, pattern in enumerate(patterns):
            matches = re.finditer(pattern, text)
            for match in matches:
                if pattern_idx == 2:
                    title = match.group(1).strip()
                    name = match.group(2).strip()
                else:
                    name = match.group(1).strip()
                    title = match.group(2).strip()
                
                name_parts = name.split()
                if not (2 <= len(name_parts) <= 4):
                    continue
                
                title = ' '.join(title.split())[:100]
                title_lower = title.lower()
                matched_title = None
                max_priority = 0
                
                for keyword, (formal_title, priority) in leadership_titles.items():
                    if keyword in title_lower:
                        if priority > max_priority:
                            matched_title = title
                            max_priority = priority
                
                if matched_title and max_priority > 0:
                    image_url = None
                    for img in images:
                        img_alt = img.get('alt', '').lower()
                        if any(word.lower() in img_alt for word in name_parts):
                            image_url = img.get('url')
                            break
                    
                    context = 'text_pattern'
                    if name not in found_leaders or found_leaders[name][1] < max_priority:
                        found_leaders[name] = (matched_title, max_priority, image_url, context)
    
    # Convert to list format
    for name, (title, priority, image_url, context) in found_leaders.items():
        leader = {
            'name': name,
            'title': title,
            'priority': priority,
            'image_url': image_url,
            'source_url': content.get('url'),
            'extracted_at': datetime.now().isoformat(),
            'extraction_context': context
        }
        
        # Add warning if from testimonials
        if context == 'testimonial' or extracted_from_testimonials:
            leader['warning'] = '⚠️ May be from testimonials, not company leadership'
        
        leaders.append(leader)
    
    # Sort by priority (highest first)
    leaders.sort(key=lambda x: x['priority'], reverse=True)
    
    # Remove priority from output (keep for internal use)
    # for leader in leaders:
    #     leader.pop('priority', None)
    
    # Add suggestion for dedicated leadership page
    if leadership_page_links and (extracted_from_testimonials or len(leaders) < 3):
        logger.warning(f"Found potential leadership pages: {leadership_page_links[:3]}")
        # Store in a way the UI can access
        content['suggested_leadership_urls'] = leadership_page_links[:5]
    
    logger.info(f"Extracted {len(leaders)} unique leadership profiles")
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
    
    with st.form(key="url_input_form"):
        url_input = st.text_input(
            "Website URL:",
            placeholder="https://example.com/about-us",
            help="Enter the URL of the webpage you want to analyze"
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
                content = scrape_url(url_input)
                
                if 'error' in content:
                    st.error(f"❌ Error scraping URL: {content['error']}")
                else:
                    st.session_state.current_url = url_input
                    st.session_state.scraped_content = content
                    st.success(f"✅ Successfully scraped: {content['title']}")
                    st.rerun()


def display_scraped_content():
    """Display scraped content summary."""
    if not st.session_state.scraped_content:
        return
    
    content = st.session_state.scraped_content
    
    st.markdown("### 📄 Scraped Content")
    
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Extract Leadership", use_container_width=True):
            with st.spinner("Extracting leadership information..."):
                leaders = extract_leadership_info(st.session_state.scraped_content)
                st.session_state.extracted_leaders = leaders
                
                if leaders:
                    st.success(f"✅ Extracted {len(leaders)} leaders")
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
        if st.button("🔄 Clear Data", use_container_width=True):
            st.session_state.scraped_content = None
            st.session_state.extracted_leaders = []
            st.session_state.current_url = None
            st.success("✅ Data cleared")
            st.rerun()


def display_extracted_leaders():
    """Display extracted leadership information with better formatting."""
    if not st.session_state.extracted_leaders:
        return
    
