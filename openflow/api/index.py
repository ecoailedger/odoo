"""
Vercel serverless function entry point for OpenFlow
"""
from openflow.server.main import app

# Vercel expects the app to be available at module level
# The variable name must be 'app' for Vercel to recognize it
handler = app
