# Railway configuration backup
import os

def get_discord_token():
    # Try environment variable first
    token = os.getenv('DISCORD_TOKEN')
    if token:
        return token
    
    # Railway backup method
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        return token
        
    # Check all possible environment variable names
    possible_names = ['DISCORD_TOKEN', 'Discord_Token', 'discord_token', 'TOKEN']
    for name in possible_names:
        token = os.getenv(name) or os.environ.get(name)
        if token:
            return token
    
    return None