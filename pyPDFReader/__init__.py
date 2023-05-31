from .pdfExtractor import pdfExtractor

from threading import Thread

def extract_PDF_parallel(fn, args, list_to_process, num_threads=10):
    threads = []
    counter = 0
    while counter < len(list_to_process)-1:
    
        if len(list_to_process) - counter < num_threads:
          list_ = list_to_process[counter:]
        else:
          list_ = list_to_process[counter:counter+num_threads]
    
        for pdf_path in list_:
            t = Thread(target=fn, args=(pdf_path, args[0], args[1]))
            threads.append(t)
            t.start()

        # wait for the threads to complete
        for t in threads:
          t.join()
        counter += num_threads
  
