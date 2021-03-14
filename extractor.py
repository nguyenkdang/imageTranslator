try:
    from PIL import Image
except ImportError:
    import Image

import pytesseract, sys, os, cv2, cropper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from google_trans_new import google_translator 
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ocrCore():
    def __init__(self, img, lang, oem=3, psm=12):
        ## img - image file
        ## psm/oem - int defining the mode of text extraction oem(0-3), psm(0-13)
        ## lang - string of language to extract (use pytesseract.get_languages() to get avaiilible languages)
        ## readFromTop/Left - bool of which region to read from 
        self.img =  img
        self.psm = psm
        self.oem = oem
        self.lang = lang
        self.readFromTop = True
        self.readFromLeft = False
    
    def getString(self):
        # Use OCR processing on images and return string of extracted text
        ## return - string of extracted text
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_string(self.img, lang=self.lang, config=config)
    
    def getData(self):
        # Use OCR processing on images and return data of extracted text
        ## return - dict of data from extracted text
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_data(self.img, lang=self.lang, config=config, output_type= pytesseract.Output.DICT)
    
    def getBox(self):
        ## Use OCR processing on images and return box of extracted letters
        ## return - string of all letters and their image cordinates
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_boxes(self.img, lang=self.lang, config=config)
    
    def exportBoxes(self, conf = 90, fnfe = None):
        # Exports a copy of the image with all the text detection boxes displayed
        ## fnfe - list/tuple where list[0] = file name and list[1] = file extension for export
        ##        if fnfn = None, will attempt to use the file name as a base for export name
        if fnfe == None: fn, fe = os.path.splitext(self.img.filename)
        else: fn, fe = fnfe
        
        #TO DO : and conf elimnator
        savePath = fn + '_' + str(self.oem) + '-' + str(self.psm) + fe        
        fig = plt.figure(frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(self.img)
        ax.axis('off')
        data = self.getData()
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) < conf: continue 
            left = data['left'][i]
            top = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            rect = patches.Rectangle((left, top), width, height, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        
        plt.savefig(savePath, bbox_inches='tight', pad_inches=0.0, dpi=200)

    def alignBoxes(self, wordList, tolerance=0.33):     
        # if text detection boxes are closed together align them according to reading style 
        ## wordList - list of [left, top, width, height, word] representing text detection box
        ## tolerance - percent of median box's dimension (width or height) that can be considered alignable
        ## return - list of [left, top, width, height, word] representing text detection box
        base = 3 #height
        start = 1 #top
        if 'vert' in self.lang:
            base  = 2 #width
            start = 0 #left
        mPos = int((len(wordList)+1)/2)

        if mPos == 0: return wordList
        median = [x[base] for x in sorted(wordList, key=lambda word: word[base])][mPos]
        medianTolerance = median * tolerance
        
        
        sortAlign = sorted(wordList, key=lambda word: word[start])
        SACopy = sortAlign
        
        while True:
            for i in range(len(sortAlign)):
                if i + 1 == len(sortAlign): continue 
                
                cur = SACopy[i][start]
                nxt = SACopy[i+1][start]
                if 'vert' in self.lang:
                    cur += SACopy[i+1][base]
                    nxt += SACopy[i+1][base]

                if nxt - cur == 0: continue
                if abs(nxt - cur) <= medianTolerance: SACopy[i+1][start] = SACopy[i][start]
            
            if SACopy == sortAlign: break
            else: sortAlign = SACopy
        
        return sortAlign
    
    def orderText(self):
        # When using using certain psm (like 11 or 12) text extracted are unordered. Reorder the extracted text
        # ordering depends on 'readfrom' class variables
        ## return - list of ordered extracted text
        data = self.getData()
        wordList = []
        areaMax, leftMax, topMax = 0, 0, 0

        for i in range(len(data['text'])):
            if int(data['conf'][i]) < 90: continue 
            left, top, width, height = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            info = [left, top, width, height, data['text'][i]]

            if left > leftMax:          leftMax = left
            if top  > topMax:           topMax = top
            if width*height > areaMax:  areaMax = width*height
            
            wordList.append(info)
        
        areaMax   = 10**len(str(areaMax))
        leftMax   = 10**len(str(leftMax))
        topMax    = 10**len(str(topMax))
        
        wordList = self.alignBoxes(wordList)
        rank = []
        for i in range(len(wordList)):
            left = wordList[i][0]
            top  = wordList[i][1]
            area = wordList[i][2] * wordList[i][3]
            if not self.readFromTop:  top = topMax - top
            if not self.readFromLeft: left = leftMax - left
            
            if 'vert' in self.lang: l = ((left * topMax) + top)  * areaMax
            else:                   l = ((top * leftMax) + left) * areaMax
            
            l += area
            rank.append((l, wordList[i][4]))

        rank = [z[1] for z in sorted(rank, key=lambda word: word[0])]
        
        return rank

    def getImage(self):
        #return - image file
        return self.img

if __name__ == "__main__":
    translator = google_translator()  
    lang='jpn_vert'

    #print(pytesseract.get_languages())
    path = os.path.join(sys.path[0], 'raw8.png')
    ePath = os.path.join(sys.path[0], 'crop')
    
    img = Image.open(path)
    cropped = cropper.getCrop(img, ePath)
    
    n = 0
    for i in cropped:
        print('bubble', n)
        ocr = ocrCore(i, lang, 3,  12)
        #extractedText = ocr.getString().strip()
        orderedText = ocr.orderText()
        combinedText = ''
        print(orderedText)
        for ot in orderedText:
            if any(c.isalpha() for c in ot):
                combinedText += ot
        
        #print(orderedText)
        tranlastedText = translator.translate(combinedText,lang_tgt='en')
        print(combinedText, '->', tranlastedText)
        
        ocr.exportBoxes(fnfe=(os.path.join(ePath, str(n)), '.jpg'))
        n += 1
        print()
