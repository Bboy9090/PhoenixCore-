"""
QR Code Recipe Scanner for PhoenixDrive
Scans QR codes from mobile app and imports recipes
"""

import json
import logging
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import cv2
    import pyzbar.pyzbar as pyzbar
    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False

logger = logging.getLogger(__name__)


@dataclass
class QRCodeData:
    """QR code data structure."""
    
    recipe_id: str
    recipe_name: str
    os_type: str
    os_version: str
    tools: list
    checksum: str
    timestamp: str
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recipe_id": self.recipe_id,
            "recipe_name": self.recipe_name,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "tools": self.tools,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QRCodeData":
        """Create from dictionary."""
        return cls(
            recipe_id=data.get("recipe_id"),
            recipe_name=data.get("recipe_name"),
            os_type=data.get("os_type"),
            os_version=data.get("os_version"),
            tools=data.get("tools", []),
            checksum=data.get("checksum"),
            timestamp=data.get("timestamp"),
            version=data.get("version", "1.0"),
        )


class QRCodeScanner:
    """QR code scanner for recipe import."""
    
    def __init__(self):
        """Initialize QR code scanner."""
        self.camera = None
        self.is_scanning = False
    
    def scan_from_camera(self, timeout_seconds: int = 30) -> Optional[QRCodeData]:
        """Scan QR code from camera."""
        if not HAS_CAMERA:
            logger.error("Camera support not available. Install opencv-python and pyzbar.")
            return None
        
        try:
            # Open camera
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return None
            
            self.is_scanning = True
            frame_count = 0
            max_frames = timeout_seconds * 30  # Assume 30 FPS
            
            while self.is_scanning and frame_count < max_frames:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Decode QR codes
                decoded_objects = pyzbar.decode(frame)
                
                if decoded_objects:
                    for obj in decoded_objects:
                        try:
                            data = obj.data.decode('utf-8')
                            qr_data = self._parse_qr_data(data)
                            if qr_data:
                                logger.info(f"Successfully scanned recipe: {qr_data.recipe_name}")
                                return qr_data
                        except Exception as e:
                            logger.error(f"Failed to parse QR code: {e}")
                
                # Display frame with bounding boxes
                for obj in decoded_objects:
                    x, y, w, h = obj.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow("QR Code Scanner", frame)
                
                # Check for ESC key
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                
                frame_count += 1
            
            return None
            
        except Exception as e:
            logger.error(f"Camera scanning failed: {e}")
            return None
        
        finally:
            self.stop_scanning()
    
    def scan_from_file(self, file_path: str) -> Optional[QRCodeData]:
        """Scan QR code from image file."""
        if not HAS_CAMERA:
            logger.error("Image processing not available. Install opencv-python and pyzbar.")
            return None
        
        try:
            # Read image
            image = cv2.imread(file_path)
            if image is None:
                logger.error(f"Failed to read image: {file_path}")
                return None
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(image)
            
            if decoded_objects:
                for obj in decoded_objects:
                    try:
                        data = obj.data.decode('utf-8')
                        qr_data = self._parse_qr_data(data)
                        if qr_data:
                            logger.info(f"Successfully scanned recipe from image: {qr_data.recipe_name}")
                            return qr_data
                    except Exception as e:
                        logger.error(f"Failed to parse QR code: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"File scanning failed: {e}")
            return None
    
    def scan_from_text(self, qr_text: str) -> Optional[QRCodeData]:
        """Scan QR code from text (manual paste)."""
        try:
            qr_data = self._parse_qr_data(qr_text)
            if qr_data:
                logger.info(f"Successfully parsed recipe from text: {qr_data.recipe_name}")
                return qr_data
            return None
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return None
    
    def _parse_qr_data(self, data: str) -> Optional[QRCodeData]:
        """Parse QR code data."""
        try:
            # Try to decode base64
            try:
                decoded = base64.b64decode(data).decode('utf-8')
                data = decoded
            except Exception:
                pass
            
            # Parse JSON
            json_data = json.loads(data)
            
            # Validate required fields
            required_fields = ["recipe_id", "recipe_name", "os_type", "checksum", "timestamp"]
            if not all(field in json_data for field in required_fields):
                logger.error("Missing required fields in QR code data")
                return None
            
            # Create QRCodeData object
            qr_data = QRCodeData.from_dict(json_data)
            
            # Validate checksum
            if not self._validate_checksum(qr_data):
                logger.warning("QR code checksum validation failed")
            
            return qr_data
            
        except json.JSONDecodeError:
            logger.error("Failed to parse QR code as JSON")
            return None
        except Exception as e:
            logger.error(f"Failed to parse QR code data: {e}")
            return None
    
    def _validate_checksum(self, qr_data: QRCodeData) -> bool:
        """Validate QR code checksum."""
        try:
            import hashlib
            
            # Create checksum data
            data_str = f"{qr_data.recipe_id}{qr_data.recipe_name}{qr_data.os_type}{qr_data.timestamp}"
            calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()[:16]
            
            return calculated_checksum == qr_data.checksum
            
        except Exception as e:
            logger.error(f"Checksum validation failed: {e}")
            return False
    
    def stop_scanning(self):
        """Stop scanning."""
        self.is_scanning = False
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
    
    def generate_qr_code(self, recipe_data: Dict[str, Any]) -> Optional[str]:
        """Generate QR code from recipe data."""
        try:
            import qrcode
            
            # Create QR code data
            qr_text = json.dumps(recipe_data)
            
            # Encode as base64
            qr_encoded = base64.b64encode(qr_text.encode()).decode()
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_encoded)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            return img
            
        except ImportError:
            logger.error("qrcode library not installed. Install with: pip install qrcode[pil]")
            return None
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return None


class RecipeImporter:
    """Import recipes from QR codes or files."""
    
    def __init__(self, recipes_dir: Optional[Path] = None):
        """Initialize recipe importer."""
        self.scanner = QRCodeScanner()
        self.recipes_dir = recipes_dir or Path.home() / ".phoenixdrive" / "recipes"
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
    
    def import_from_camera(self) -> Optional[Dict[str, Any]]:
        """Import recipe from camera QR code."""
        qr_data = self.scanner.scan_from_camera()
        if qr_data:
            return self._save_recipe(qr_data)
        return None
    
    def import_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Import recipe from image file."""
        qr_data = self.scanner.scan_from_file(file_path)
        if qr_data:
            return self._save_recipe(qr_data)
        return None
    
    def import_from_text(self, qr_text: str) -> Optional[Dict[str, Any]]:
        """Import recipe from text."""
        qr_data = self.scanner.scan_from_text(qr_text)
        if qr_data:
            return self._save_recipe(qr_data)
        return None
    
    def _save_recipe(self, qr_data: QRCodeData) -> Dict[str, Any]:
        """Save recipe to file."""
        try:
            recipe_file = self.recipes_dir / f"{qr_data.recipe_id}.json"
            
            recipe_dict = qr_data.to_dict()
            with open(recipe_file, 'w') as f:
                json.dump(recipe_dict, f, indent=2)
            
            logger.info(f"Recipe saved to {recipe_file}")
            return recipe_dict
            
        except Exception as e:
            logger.error(f"Failed to save recipe: {e}")
            return {}
    
    def list_recipes(self) -> list:
        """List all imported recipes."""
        try:
            recipes = []
            for recipe_file in self.recipes_dir.glob("*.json"):
                with open(recipe_file, 'r') as f:
                    recipe = json.load(f)
                    recipes.append(recipe)
            return recipes
        except Exception as e:
            logger.error(f"Failed to list recipes: {e}")
            return []
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe by ID."""
        try:
            recipe_file = self.recipes_dir / f"{recipe_id}.json"
            if recipe_file.exists():
                with open(recipe_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to get recipe: {e}")
            return None
