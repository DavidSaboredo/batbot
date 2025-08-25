# Overview

BatCompany Discord Bot is a PUBG-focused Discord bot that implements a progressive role system based on voice channel activity. The bot monitors users in specific PUBG voice channels and automatically assigns themed roles (Murci-Casual, Ala Chueca, Eco-Legend, Dark Commander) based on cumulative time spent in voice channels. It features a web dashboard for live monitoring and is designed for 24/7 operation on Replit hosting.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Discord.py**: Core Discord bot functionality with commands extension
- **Intents**: Voice states, guilds, and members intents enabled for voice channel monitoring
- **Command Prefix**: Uses `!` prefix for bot commands

## Progressive Role System
- **Time-based Progression**: Four-tier role system with increasing time requirements (30 minutes to 10 hours)
- **Voice Channel Monitoring**: Tracks user activity in specified PUBG voice channels only
- **Automatic Role Assignment**: Bot assigns roles based on cumulative voice connection time
- **Role Hierarchy**: Each role has custom colors and Spanish-language descriptions with gaming themes

## Web Dashboard
- **Flask Web Server**: Provides live status dashboard accessible via browser
- **Bootstrap Frontend**: Responsive web interface with Discord-themed styling
- **Real-time Stats**: Displays bot uptime, connected users, and role distribution
- **Threading**: Web server runs in separate thread to maintain bot functionality

## Hosting Architecture
- **Replit Deployment**: Designed for Replit hosting with keepalive functionality
- **Environment Variables**: Discord token stored in Replit Secrets for security
- **24/7 Uptime**: Flask server prevents Replit from sleeping the application

## Data Management
- **In-memory Storage**: User voice connection times stored in bot memory (no persistent database)
- **Session-based Tracking**: Tracks voice state changes and calculates cumulative time
- **Role State Management**: Maintains current role assignments and prevents duplicate assignments

# External Dependencies

## Discord Integration
- **Discord Bot API**: Primary integration for bot functionality and server management
- **Required Permissions**: View channels, send messages, manage roles, voice channel access
- **Bot Token**: Requires Discord bot token from Discord Developer Portal

## Web Framework
- **Flask**: Lightweight web framework for dashboard functionality
- **Bootstrap 5.1.3**: Frontend CSS framework from CDN
- **Font Awesome 6.0.0**: Icon library from CDN

## Python Libraries
- **discord.py**: Discord API wrapper and bot framework
- **asyncio**: Asynchronous programming support for Discord events
- **threading**: Multi-threading support for web server

## Hosting Requirements
- **Replit Environment**: Designed specifically for Replit hosting platform
- **Secrets Management**: Uses Replit Secrets for secure token storage
- **Keepalive Server**: Flask server prevents application hibernation

## Configuration Dependencies
- **Voice Channel IDs**: Requires manual configuration of Discord voice channel IDs
- **Role Hierarchy**: Bot role must be positioned above managed roles in Discord server