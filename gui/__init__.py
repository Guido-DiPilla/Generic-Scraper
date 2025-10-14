"""
GUI components package for Generic Scraper.
Provides modular GUI components for better code organization.
"""

from .client_generation import ClientGenerator, FileManager
from .config_tabs import AdvancedTab, BasicTab, FieldsTab, PreviewTab, WebsiteTab
from .field_dialog import FieldMappingDialog
from .output_formatting import OutputFormatter, ProgressTracker
from .scraper_tab import ScraperTab
from .tooltip import ToolTip

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
