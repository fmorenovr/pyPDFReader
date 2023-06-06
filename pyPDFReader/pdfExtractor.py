
try:
    import Image
except ImportError:
    from PIL import Image

import pytesseract

from pdf2image import convert_from_path

import io
import fitz
import pdfplumber

import logging

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

#from py.nlpToolkit.nlpToolkit.language_processing import LanguageProcesser

class pdfExtractor:
    def __init__(self, pdf_path=None, 
                       set_page_limiter=False, 
                       language="portuguese", 
                       TMP_OUT_PATH=None, 
                       language_processer=None, 
                       acceptable_ratio = 0.65,
                       page_scaler=2.54,
                       no_margin = True,
                       margin_left = 1.2, 
                       margin_top = 2, 
                       margin_right = 1.2, 
                       margin_bot = 2):
                       
        self.pdf_path = pdf_path
        self.set_page_limiter = set_page_limiter
        self.language = language
        self.TMP_OUT_PATH=TMP_OUT_PATH
        
        self.acceptable_ratio = acceptable_ratio
        self.page_scaler = page_scaler
        
        self.no_margin = no_margin
        self.margin_left = margin_left
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bot = margin_bot
        
        #self.language_processer = LanguageProcesser(languages_to_eval=self.language)
        self.language_processer = language_processer
        
        self.split_regex = "(?:(?:\s*\n\s*){2,}|(?<=[\.:])\s*\n\s*)"
        
    def set_pdf(self, pdf_path):
        self.pdf_path = pdf_path
    
    def pdf_evaluate(self, pdf_path):
        content, num_pages, opened = self.pymupdf_extractText(pdf_path)
        self.verifyLanguage(content)
        logging.info(f"PyMuPDF ratio: {self.language_ratio}")
        logging.info(f"PyMuPDF correct-incorrect words: {len(self.correct_words)}-{len(self.incorrect_words)}")
        logging.info(f"PyMuPDF incorrect words: {self.incorrect_words}")
        
        if num_pages>0 and opened and self.language_ratio >= self.acceptable_ratio and len(content)>0:
            logging.info("PyMuPDF should be used")
            return content, "PYMU"

        logging.info("OCR should be used")         
        return content, "OCR"
        
    def pdf_extractText(self, pdf_path, method="PYMU"):
        if method == "PYMU":
            content, num_pages, opened = self.pymupdf_extractText(pdf_path)
            self.verifyLanguage(content)
            logging.info(f"PyMuPDF ratio: {self.language_ratio}")
            logging.info(f"PyMuPDF incorrect words: {self.incorrect_words}")
        
            if num_pages>0 and opened and self.language_ratio >= self.acceptable_ratio and len(content)>0:
                logging.info("PyMuPDF used")
                return content, "PYMU"
            else:
                None, None
        else:
            content, num_pages, opened = self.ocr_extractText(pdf_path)
            self.verifyLanguage(content)
            logging.info(f"OCR ratio: {self.language_ratio}")
            logging.info(f"OCR correct-incorrect words: {len(self.correct_words)}-{len(self.incorrect_words)}")
            logging.info(f"OCR incorrect words: {self.incorrect_words}")
            
            #if num_pages>0 and opened and self.language_ratio >= 0.6:
            logging.info("OCR used")
            return content, "OCR"
        
        return None, None
    
    def pdf_eval_and_extractText(self, pdf_path):
        content, num_pages, opened = self.pymupdf_extractText(pdf_path)
        self.verifyLanguage(content)
        logging.info(f"PyMuPDF ratio: {self.language_ratio}")
        logging.info(f"PyMuPDF incorrect words: {self.incorrect_words}")
        
        if num_pages>0 and opened and self.language_ratio >= self.acceptable_ratio and len(content)>0:
            logging.info("PyMuPDF used")
            return content, "PYMU"
        else:
            content, num_pages, opened = self.ocr_extractText(pdf_path)
            self.verifyLanguage(content)
            logging.info(f"OCR ratio: {self.language_ratio}")
            logging.info(f"OCR correct-incorrect words: {len(self.correct_words)}-{len(self.incorrect_words)}")
            logging.info(f"OCR incorrect words: {self.incorrect_words}")
            
            #if num_pages>0 and opened and self.language_ratio >= 0.6:
            logging.info("OCR used")
            return content, "OCR"
        
        return None, None
    
    # return list of correct words in the most rated language
    def get_correct_words(self):        
        return self.correct_words
    
    # return list of incorrect words in the most rated language
    def get_incorrect_words(self): 
        return self.incorrect_words
    
    def verifyLanguage(self, content, ratio=0.9):
        
        if self.language_processer is not None:
        
            self.language_processer.detect_language_and_word_list(content)
            
            self.pt_ratio = self.language_processer.get_language_ratios()
            self.correct_words = self.language_processer.get_correct_words()
            self.incorrect_words = self.language_processer.get_incorrect_words()
            self.language_ratio = self.pt_ratio[self.language]
        
        else:
            self.pt_ratio = None
            self.correct_words = None
            self.incorrect_words = None
            self.language_ratio = None

    def pdf_to_img(self, pdf_path):
        pdf_name = (pdf_path.split("/")[-1]).split(".pdf")[0]
        images = convert_from_path(pdf_path)
        
        for i in range(len(images)):
            images[i].save(f'{self.TMP_OUT_PATH}{pdf_name}_page_{str(i)}.jpg', 'JPEG')
        
        return images

    def ocr_extractText(self, pdf_path):
        # sudo apt install tesseract-ocr 
        # sudo apt-get install tesseract-ocr-all
        # sudo apt-get install libtesseract-dev
        # pip install pytesseract
        pdf_name = (pdf_path.split("/")[-1]).split(".pdf")[0]
        content = ''
        num_pages=0
        opened = False
        
        try:
            logging.info("Using OCR")
            pdf_images = convert_from_path(pdf_path)
            num_pages = len(images)
        
            for current_image in pdf_images:
            
                if not self.no_margin:
                
                    dpi_x = 72
                    dpi_y = 72
                
                    width, height = current_image.size
                    
                    x1 = int( self.margin_left*dpi_x/self.page_scaler )
                    y1 = int( self.margin_top*dpi_y/self.page_scaler )
                    
                    x2 = width - int( self.margin_right*dpi_x/self.page_scaler )
                    y2 = height - int( self.margin_bot*dpi_y/self.page_scaler )

                    cropped_image = current_image.crop((x1, y1, x2, y2))
                #images[i].save(f'{path_to_save}{pdf_name}_page_{str(i)}.jpg', 'JPEG')
                # Optical Character Recognition
                    page_content = pytesseract.image_to_string(cropped_image, lang="por")
                else:
                    page_content = pytesseract.image_to_string(current_image, lang="por")
                
                if self.set_page_limiter:
                  text_ = page_content + "\nENDOFPAGE\n"
                else:
                  text_ = page_content + "\n\n"
                
                content += text_
                content = content.strip("\n")

            opened = True
        
        except Exception as e:
            logging.error(f"OCR error: {e}")
            opened = False
            content = ''
            num_pages=0
        
        return content, num_pages, opened
        
    def pymupdf_extractText(self, pdf_path):
        pdf_name = (pdf_path.split("/")[-1]).split(".pdf")[0]
        content = ''
        num_pages=0
        opened = False
        
        try:
            logging.info("Using PyMuPDF")
            with fitz.open(pdf_path) as pdf:
              num_pages = len(pdf)
              cur_page=0
              for page in pdf:
                
                if not self.no_margin:
                    
                    dpi_x = 72
                    dpi_y = 72
                    
                    width, height = page.rect.width, page.rect.height
                
                    x1 = int( self.margin_left*dpi_x/self.page_scaler )
                    y1 = int( self.margin_top*dpi_y/self.page_scaler )
                    
                    x2 = width - int( self.margin_right*dpi_x/self.page_scaler )
                    y2 = height - int( self.margin_bot*dpi_y/self.page_scaler )
                    
                    current_rect = fitz.Rect(x1, y1, x2, y2)
                    block_content = page.get_text("blocks", clip=current_rect)
                    page_content = "\n".join(b[4] for b in block_content)
                else:
                    page_content = page.get_text()
              
                if self.set_page_limiter:
                  text_ = page_content + "\nENDOFPAGE\n"
                else:
                  text_ = page_content + "\n\n"
                  
                content += text_
                content = content.strip("\n")

            opened = True
          
        except Exception as e:
            logging.error(f"PyMUPDF error: {e}")
            opened = False
            content = ''
            num_pages=0
          
        return content, num_pages, opened
   
    def pdfplumber_extract_txt(self, pdf_path):
        pdf_name = (pdf_path.split("/")[-1]).split(".pdf")[0]
        content = ''
        num_pages=0
        opened = False

        try:
          with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            cur_page=0
            while cur_page<num_pages:
              if self.set_page_limiter:
                text_ = pdf.pages[cur_page].extract_text() + "\nENDOFPAGE\n"
              else:
                text_ = pdf.pages[cur_page].extract_text() + "\n\n"
              content += text_
              cur_page = cur_page+1

          opened = True

        except Exception as e:
            logging.erro(e)
            opened = False
            content = ''
            num_pages=0
          
        return content, num_pages, opened
    
    def pdfminer_extractText(path, to_save=True, path_to_save="../../data/STF/CSV/", set_page_limiter=False):
        rsrcmgr = PDFResourceManager()
        retstr = io.StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                      password=password,
                                      caching=caching,
                                      check_extractable=True):
          interpreter.process_page(page)

        fp.close()
        device.close()
        text = retstr.getvalue()
        retstr.close()
        return text
   
