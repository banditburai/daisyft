"""
GitHub release information for Tailwind binaries.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class TailwindReleaseInfo:
    """Information about Tailwind releases and repositories."""
        
    DAISY_REPO = "dobicinaitis/tailwind-cli-extra"
    VANILLA_REPO = "tailwindlabs/tailwindcss"
    
    
    @classmethod
    def get_api_url(cls, style: str = "daisy") -> str:
        if style == "daisy":
            return f"https://api.github.com/repos/{cls.DAISY_REPO}/releases/latest"
        else:            
            return f"https://api.github.com/repos/{cls.VANILLA_REPO}/releases/latest"
    
    @classmethod
    def get_download_url(cls, style: str = "daisy") -> str:
        if style == "daisy":
            return f"https://github.com/{cls.DAISY_REPO}/releases/latest/download/"
        else:
            return f"https://github.com/{cls.VANILLA_REPO}/releases/latest/download/" 