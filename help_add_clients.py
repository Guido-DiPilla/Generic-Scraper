#!/usr/bin/env python3
"""
Help script for adding new clients to the Generic Scraper
"""

print("""
🚀 Generic Scraper - Adding New Clients
=======================================

You now have TWO ways to add new scraping clients:

📱 METHOD 1: GUI Client Generator (Recommended)
   ./venv/bin/python generate_client.py
   
   ✅ User-friendly graphical interface
   ✅ Form-based input with validation
   ✅ Field mapping editor with drag & drop
   ✅ Live code preview
   ✅ Save/load templates
   ✅ Built-in help and examples

💻 METHOD 2: CLI Client Generator (For servers/headless)
   ./venv/bin/python generate_client_cli.py
   
   ✅ Command-line interface
   ✅ Interactive prompts
   ✅ Works on servers without GUI
   ✅ Same functionality as GUI version

📋 What Both Tools Do:
   • Guide you through client configuration
   • Generate the client .py file automatically
   • Update the clients registry
   • Validate input and check for conflicts
   • Your new client appears instantly in the scraper menu!

🎯 After Creating a Client:
   • Test it: ./venv/bin/python generic_scrape.py --client your_client_id
   • It appears in the interactive menu automatically
   • All the same features: proxy, progress, resume, etc.

📖 Manual Method (Advanced):
   1. Copy clients/example_client_template.py
   2. Modify the configuration for your website
   3. Add import/registration to clients/__init__.py

💡 Need Help?
   • Check the example_client_template.py for reference
   • Look at existing clients (g2s_client.py, demo_client.py)
   • Field mappings use CSS selectors
   • Transform functions: clean_text, extract_numeric, normalize_part

Happy scraping! 🕷️
""")