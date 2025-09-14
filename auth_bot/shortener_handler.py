#!/usr/bin/env python3
"""
Auth Bot Shortener Handler
Manages shortener integration for verification system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from urllib.parse import quote
import uuid
import sys
from pathlib import Path
import os

try:
    import cloudscraper
except ImportError:
    logging.warning("cloudscraper not available, shortener functionality will be limited")

# Local shortener configuration for auth bot
shorteners_list = []

# Load shorteners from local file
shorteners_file = Path(__file__).parent / "shorteners.txt"
if shorteners_file.exists():
    with open(shorteners_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                temp = line.split()
                if len(temp) >= 2:
                    shorteners_list.append({"domain": temp[0], "api_key": temp[1]})

def short_url(url, attempt=0):
    """URL shortener using configured services with real API calls"""
    if not shorteners_list or not url:
        return url
    
    if attempt >= 4:
        return url
    
    try:
        # Try each configured shortener
        import cloudscraper
        from urllib.parse import quote
        
        for shortener in shorteners_list:
            try:
                domain = shortener["domain"]
                api_key = shortener["api_key"]
                
                # Create cloudscraper session
                scraper = cloudscraper.create_scraper()
                
                if "gplinks.com" in domain:
                    # GPLinks API call
                    api_url = f"https://gplinks.com/api?api={api_key}&url={quote(url)}"
                    response = scraper.get(api_url, timeout=10)
                    data = response.json()
                    
                    if data.get("shortenedUrl"):
                        logging.info(f"Successfully shortened URL with GPLinks: {data['shortenedUrl']}")
                        return data["shortenedUrl"]
                        
                elif "ouo.io" in domain:
                    # OUO.io API call
                    api_url = f"http://ouo.io/api/{api_key}?s={url}"
                    response = scraper.get(api_url, verify=False, timeout=10)
                    if response.text and response.text.startswith("http"):
                        logging.info(f"Successfully shortened URL with OUO: {response.text.strip()}")
                        return response.text.strip()
                        
                # Add more shortener implementations as needed
                
            except Exception as e:
                logging.error(f"Shortener {domain} failed: {e}")
                continue
        
    except ImportError:
        logging.error("cloudscraper not available, cannot use real shortener APIs")
    except Exception as e:
        logging.error(f"Shortener error: {e}")
    
    # If all shorteners fail, return original URL
    logging.warning("All shorteners failed, returning original URL")
    return url

class AuthShortenerManager:
    """Manages shortener verification for auth bot"""
    
    def __init__(self):
        self.active_verifications = {}  # user_id: {shortener_id, verification_data}
        self.user_shortener_cooldowns = {}  # user_id: {shortener_id: expires_at}
        
    def get_configured_shorteners(self):
        """Get list of configured shortener services from local file"""
        if not shorteners_list:
            # Return empty list if no shorteners configured
            logging.warning("No shorteners configured in shorteners.txt")
            return []
        
        # Convert local shorteners to our format
        configured = []
        for i, shortener in enumerate(shorteners_list):
            configured.append({
                "id": i + 1,
                "domain": shortener["domain"],
                "name": shortener["domain"].replace(".com", "").replace(".io", "").replace(".ly", "").title(),
                "api_key": shortener["api_key"]
            })
        
        return configured
    
    def get_available_shorteners_for_user(self, user_id):
        """Get shorteners available for user (excluding those on cooldown)"""
        all_shorteners = self.get_configured_shorteners()
        available = []
        now = datetime.now()
        
        for shortener in all_shorteners:
            shortener_id = shortener["id"]
            
            # Check if shortener is on cooldown for this user
            if (user_id in self.user_shortener_cooldowns and 
                shortener_id in self.user_shortener_cooldowns[user_id]):
                cooldown_expires = self.user_shortener_cooldowns[user_id][shortener_id]
                if datetime.fromisoformat(cooldown_expires) > now:
                    continue  # Skip this shortener, still on cooldown
            
            available.append(shortener)
        
        return available
    
    def is_user_locked_to_shortener(self, user_id):
        """Check if user must complete current shortener verification first"""
        return user_id in self.active_verifications
    
    def get_user_locked_shortener(self, user_id):
        """Get the shortener user is currently locked to"""
        if user_id in self.active_verifications:
            return self.active_verifications[user_id].get("shortener_id")
        return None
    
    def start_verification_session(self, user_id, shortener_id, bot_key, token_type="single", additional_data=None):
        """Start a new verification session for user"""
        verification_token = str(uuid.uuid4())
        
        verification_data = {
            "shortener_id": shortener_id,
            "verification_token": verification_token,
            "bot_key": bot_key,
            "token_type": token_type,
            "started_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # Add any additional data
        if additional_data:
            verification_data.update(additional_data)
        
        self.active_verifications[user_id] = verification_data
        return verification_token
    
    def generate_verification_url(self, user_id, shortener_id, verification_token):
        """Generate verification URL using specified shortener"""
        # Create a simple verification URL that redirects to the auth bot
        base_url = f"https://t.me/Soulkaizer_bot?start=verify_{verification_token}_{user_id}"
        
        # Use main bot's shortener system
        try:
            shortened_url = short_url(base_url)
            # Validate that the shortened URL is different from the base URL
            if shortened_url and shortened_url != base_url and "http" in shortened_url:
                return shortened_url
            else:
                # If shortening failed, return the direct verification URL
                logging.warning(f"Shortener failed, using direct URL")
                return base_url
        except Exception as e:
            logging.error(f"Shortener error: {e}")
            return base_url  # Return original URL if shortening fails
    
    def complete_verification(self, user_id, verification_token):
        """Mark verification as complete and set cooldown"""
        if user_id not in self.active_verifications:
            return False
        
        verification_data = self.active_verifications[user_id]
        if verification_data["verification_token"] != verification_token:
            return False
        
        # Mark as completed
        verification_data["status"] = "completed"
        verification_data["completed_at"] = datetime.now().isoformat()
        
        # Set cooldown for this shortener (6 hours)
        shortener_id = verification_data["shortener_id"]
        cooldown_expires = datetime.now() + timedelta(hours=6)
        
        if user_id not in self.user_shortener_cooldowns:
            self.user_shortener_cooldowns[user_id] = {}
        
        self.user_shortener_cooldowns[user_id][shortener_id] = cooldown_expires.isoformat()
        
        # Clear active verification
        del self.active_verifications[user_id]
        
        return verification_data
    
    def verify_completion(self, user_id, verification_token):
        """Check if verification was completed successfully"""
        if user_id not in self.user_shortener_cooldowns:
            return False
        
        # Check if any verification matches this token and is completed
        # This is a simple implementation - in production you'd want better tracking
        return True  # For now, assume verification via start command means success
    
    def get_user_verification_count(self, user_id):
        """Get number of shorteners user has verified (not on cooldown)"""
        if user_id not in self.user_shortener_cooldowns:
            return 0
        
        now = datetime.now()
        active_verifications = 0
        
        for shortener_id, expires_at in self.user_shortener_cooldowns[user_id].items():
            if datetime.fromisoformat(expires_at) > now:
                active_verifications += 1
        
        return active_verifications
    
    def calculate_total_access_time(self, user_id):
        """Calculate total access time based on verified shorteners"""
        verification_count = self.get_user_verification_count(user_id)
        
        # Each verification adds 6 hours, max 24 hours
        total_hours = min(verification_count * 6, 24)
        return timedelta(hours=total_hours)
    
    def get_verification_summary(self, user_id):
        """Get verification status summary for user"""
        available_shorteners = self.get_available_shorteners_for_user(user_id)
        verification_count = self.get_user_verification_count(user_id)
        total_access_time = self.calculate_total_access_time(user_id)
        locked_shortener = self.get_user_locked_shortener(user_id)
        
        return {
            "available_shorteners": available_shorteners,
            "verification_count": verification_count,
            "total_access_hours": int(total_access_time.total_seconds() // 3600),
            "locked_to_shortener": locked_shortener,
            "max_verifications_reached": verification_count >= 4
        }
    
    def cleanup_expired_cooldowns(self):
        """Clean up expired shortener cooldowns"""
        now = datetime.now()
        for user_id in list(self.user_shortener_cooldowns.keys()):
            user_cooldowns = self.user_shortener_cooldowns[user_id]
            
            # Remove expired cooldowns
            expired_shorteners = []
            for shortener_id, expires_at in user_cooldowns.items():
                if datetime.fromisoformat(expires_at) <= now:
                    expired_shorteners.append(shortener_id)
            
            for shortener_id in expired_shorteners:
                del user_cooldowns[shortener_id]
            
            # Remove user entry if no active cooldowns
            if not user_cooldowns:
                del self.user_shortener_cooldowns[user_id]
