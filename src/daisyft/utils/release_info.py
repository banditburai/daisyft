"""
GitHub release information for Tailwind binaries.
"""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class TailwindReleaseInfo:
    """Information about Tailwind releases and repositories."""
    
    # Repository information
    DAISY_REPO = "banditburai/fastwindcss"
    VANILLA_REPO = "tailwindlabs/tailwindcss"
    
    
    @classmethod
    def get_api_url(cls, style: str = "daisy") -> str:
        """
        Get the GitHub API URL for release information.
        
        Args:
            style: Either "daisy" or "vanilla" to determine which repository to use
            
        Returns:
            GitHub API URL for the release
        """
        if style == "daisy":
            return f"https://api.github.com/repos/{cls.DAISY_REPO}/releases/latest"
        else:
            # For vanilla, we use a specific version tag
            return f"https://api.github.com/repos/{cls.VANILLA_REPO}/releases/latest"
    
    @classmethod
    def get_download_url(cls, style: str = "daisy") -> str:
        """
        Get the base URL for downloading binaries.
        
        Args:
            style: Either "daisy" or "vanilla" to determine which repository to use
            
        Returns:
            Base URL for downloading binaries
        """
        if style == "daisy":
            return f"https://github.com/{cls.DAISY_REPO}/releases/latest/download/"
        else:
            return f"https://github.com/{cls.VANILLA_REPO}/releases/latest/download/" 