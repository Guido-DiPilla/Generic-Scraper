# Package marker

# Simply export all functions needed
__all__ = ['process_part_number', 'fetch']

# Import functions directly
try:
    from .generic_scraper import fetch, process_part_number
except ImportError:
    # Make test collection possible even if imports fail
    pass
