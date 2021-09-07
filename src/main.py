try:
    from PIL import Image
except ImportError:
    import Image

import sys, os
from extractor import ocrPage, ocrPanel, translateList

if __name__ == "__main__":
    #print(pytesseract.get_languages())
    lang='jpn_vert'
    path = os.path.join(sys.path[0], '../input/raw8.png')
    img = Image.open(path)
    
    ocr = ocrPage(img, lang, 3,  12)
    allOrdered = ocr.orderAllText()
    
    for txt in allOrdered:    
        tranlastedText = translateList(txt)[1]
        originalText = translateList(txt)[0]
        print(originalText, '->', tranlastedText, '\n')
    ocr.cover(img)