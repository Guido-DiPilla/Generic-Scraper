# Package marker

# Export main functions for backward compatibility with tests
from .generic_scraper import fetch, process_part_number

__all__ = ['process_part_number', 'fetch']
