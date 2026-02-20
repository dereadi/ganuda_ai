import cv2
import numpy as np
import pytesseract
from collections import Counter
from typing import Tuple, List

class PlateReader:
    """
    A class for preprocessing and reading license plates using OpenCV and Tesseract OCR.
    """
    def __init__(self):
        self.tesseract_config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.recent_reads: List[str] = []

    def preprocess_plate(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Preprocesses the input license plate image to enhance readability for OCR.

        :param plate_image: Input image of the license plate.
        :return: Preprocessed binary image of the license plate.
        """
        # Convert to grayscale if the image is in color
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY) if len(plate_image.shape) == 3 else plate_image
        # Apply CLAHE for contrast limited adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)
        # Convert to binary image using Otsu's thresholding
        _, binary = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def read_plate(self, plate_image: np.ndarray) -> Tuple[str, float]:
        """
        Reads the license plate number from the preprocessed image.

        :param plate_image: Input image of the license plate.
        :return: A tuple containing the most likely license plate number and its confidence score.
        """
        processed = self.preprocess_plate(plate_image)
        # Use Tesseract to extract text from the processed image
        text = pytesseract.image_to_string(processed, config=self.tesseract_config)
        # Clean the extracted text to include only alphanumeric characters
        clean = "".join(c for c in text.upper() if c.isalnum())
        # Store recent reads and maintain a buffer of up to 5 readings
        if len(clean) >= 4:
            self.recent_reads.append(clean)
            if len(self.recent_reads) > 5:
                self.recent_reads.pop(0)
        # Determine the most common plate number from recent reads
        if len(self.recent_reads) >= 3:
            counter = Counter(self.recent_reads)
            most_common, count = counter.most_common(1)[0]
            return most_common, count / len(self.recent_reads)
        return clean, 0.5