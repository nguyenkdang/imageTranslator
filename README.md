# imageTranslator

## Summary
Image Translator is a Python script that uses a version of Google's Tesseract OCR to take and image with foreign text and translate them to a language of the user's desire. The steps to achieving this is as follow: (1) Extract text from an image using Google's Tesseract OCR, (2) Translate them to the appropriate language, (3) use language processing to increase readability, (4) overlay the translated text onto a copy of the image. Correctly calibrating Google's Tesseract OCR is critical to correctly translating the extracted text. Formatting the final image is also important, so the script makes sure to try to only cover text elements with their translated version, and not any other visuals.
