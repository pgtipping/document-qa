import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Any, Dict


class ErrorLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up file handler
        self.logger = logging.getLogger("document_qa")
        self.logger.setLevel(logging.ERROR)
        
        # Create handlers
        self._setup_file_handler()
        self._setup_error_tracking()

    def _setup_file_handler(self):
        """Set up file handler for logging."""
        log_file = self.log_dir / f"errors_{datetime.now():%Y%m%d}.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _setup_error_tracking(self):
        """Set up error tracking file."""
        self.error_file = self.log_dir / "error_tracking.json"
        if not self.error_file.exists():
            self._save_error_tracking({
                "total_errors": 0,
                "error_types": {},
                "last_updated": str(datetime.now())
            })

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        source: str
    ) -> None:
        """Log an error with context."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Log to file
        self.logger.error(
            f"Error in {source}: {error_type} - {error_msg}",
            extra={"context": context}
        )
        
        # Update error tracking
        self._update_error_tracking(error_type)

    def _update_error_tracking(self, error_type: str) -> None:
        """Update error tracking statistics."""
        tracking = self._load_error_tracking()
        
        tracking["total_errors"] += 1
        tracking["error_types"][error_type] = (
            tracking["error_types"].get(error_type, 0) + 1
        )
        tracking["last_updated"] = str(datetime.now())
        
        self._save_error_tracking(tracking)

    def _load_error_tracking(self) -> Dict[str, Any]:
        """Load error tracking data."""
        with open(self.error_file) as f:
            return json.load(f)

    def _save_error_tracking(self, data: Dict[str, Any]) -> None:
        """Save error tracking data."""
        with open(self.error_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors."""
        return self._load_error_tracking()


# Global error logger instance
error_logger = ErrorLogger() 