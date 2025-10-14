"""
GUI components package for Generic Scraper.
Provides modular GUI components for better code organization.
"""

from .tooltip import ToolTip
from .field_dialog import FieldMappingDialog
from .scraper_tab import ScraperTab
from .config_tabs import BasicTab, WebsiteTab, FieldsTab, AdvancedTab, PreviewTab
from .client_generation import ClientGenerator, FileManager
from .output_formatting import OutputFormatter, ProgressTracker

__all__ = [
    'ToolTip',
    'FieldMappingDialog', 
    'ScraperTab',
    'BasicTab',
    'WebsiteTab', 
    'FieldsTab',
    'AdvancedTab',
    'PreviewTab',
    'ClientGenerator',
    'FileManager',
    'OutputFormatter',
    'ProgressTracker'
]