import re
from src.processors.base_parser import BaseComponentParser

class MonoZoomParser(BaseComponentParser):
    # OPTIONS: 
    
    # Empty since it's a system component that just includes its assets globally
    START_PATTERN = re.compile(r"")
    FAST_PATH_MARKERS = ()

    def process(self, markdown_content: str) -> str:
        # Does not process any markdown tokens, acts as auto-included system component
        return markdown_content
